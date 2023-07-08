#
# This source file is part of the EdgeDB open source project.
#
# Copyright 2023-present MagicStack Inc. and the EdgeDB authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from __future__ import annotations
from typing import *

import asyncio
import contextlib
import functools
import logging
import sys
import time

from edb.common import taskgroup

from . import defines
from . import metrics
from . import pgcon
from .pgcon import errors as pgcon_errors

if TYPE_CHECKING:
    from edb.pgsql import params as pgparams

    from . import pgcluster
    from . import server as edbserver


logger = logging.getLogger("edb.server")


class Tenant:
    _server: edbserver.Server
    _cluster: pgcluster.BaseCluster
    _tenant_id: str
    _running: bool
    _accepting_connections: bool

    __loop: asyncio.AbstractEventLoop
    _task_group: taskgroup.TaskGroup | None
    _tasks: Set[asyncio.Task]
    _accept_new_tasks: bool

    __sys_pgcon: pgcon.PGConnection | None
    _sys_pgcon_waiter: asyncio.Lock
    _sys_pgcon_ready_evt: asyncio.Event
    _sys_pgcon_reconnect_evt: asyncio.Event

    def __init__(
        self,
        cluster: pgcluster.BaseCluster,
    ):
        self._cluster = cluster
        self._tenant_id = self.get_backend_runtime_params().tenant_id
        self._running = False
        self._accepting_connections = False

        self._task_group = None
        self._tasks = set()
        self._accept_new_tasks = False

        # Never use `self.__sys_pgcon` directly; get it via
        # `async with self.use_sys_pgcon()`.
        self.__sys_pgcon = None

    def set_server(self, server: edbserver.Server) -> None:
        self._server = server
        self.__loop = server.get_loop()

    def on_switch_over(self):
        if self.__sys_pgcon is None:
            # Assume a reconnect task is already running, now that we know the
            # new master is likely ready, let's just give the task a push.
            self._sys_pgcon_reconnect_evt.set()
        else:
            # Brutally close the sys_pgcon to the old master - this should
            # trigger a reconnect task.
            self.__sys_pgcon.abort()

    @property
    def server(self) -> edbserver.Server:
        return self._server

    @property
    def tenant_id(self) -> str:
        return self._tenant_id

    def get_pg_dbname(self, dbname: str) -> str:
        return self._cluster.get_db_name(dbname)

    def get_pgaddr(self) -> Dict[str, Any]:
        return self._cluster.get_connection_spec()

    @functools.lru_cache
    def get_backend_runtime_params(self) -> pgparams.BackendRuntimeParams:
        return self._cluster.get_runtime_params()

    def is_accepting_connections(self) -> bool:
        return self._accepting_connections and self._accept_new_tasks

    async def init_sys_pgcon(self) -> None:
        self.__sys_pgcon = await self._pg_connect(defines.EDGEDB_SYSTEM_DB)
        self._sys_pgcon_waiter = asyncio.Lock()
        self._sys_pgcon_ready_evt = asyncio.Event()
        self._sys_pgcon_reconnect_evt = asyncio.Event()

    async def start_sys_pgcon(self) -> None:
        assert self.__sys_pgcon is not None
        await self.__sys_pgcon.listen_for_sysevent()
        self.__sys_pgcon.mark_as_system_db()
        self._sys_pgcon_ready_evt.set()

    async def start_accepting_new_tasks(self) -> None:
        assert self._task_group is None
        self._task_group = taskgroup.TaskGroup()
        await self._task_group.__aenter__()
        self._accept_new_tasks = True
        await self._cluster.start_watching(self._server.on_switch_over)

    def start_running(self) -> None:
        self._running = True
        self._accepting_connections = True

    def stop_accepting_connections(self) -> None:
        self._accepting_connections = False

    @property
    def accept_new_tasks(self):
        return self._accept_new_tasks

    def create_task(
        self, coro: Coroutine, *, interruptable: bool
    ) -> asyncio.Task:
        # Interruptable tasks are regular asyncio tasks that may be interrupted
        # randomly in the middle when the event loop stops; while tasks with
        # interruptable=False are always awaited before the server stops, so
        # that e.g. all finally blocks get a chance to execute in those tasks.
        # Therefore, it is an error trying to create a task while the server is
        # not expecting one, so always couple the call with an additional check
        if self._accept_new_tasks and self._task_group is not None:
            if interruptable:
                rv = self.__loop.create_task(coro)
            else:
                rv = self._task_group.create_task(coro)

            # Keep a strong reference of the created Task
            self._tasks.add(rv)
            rv.add_done_callback(self._tasks.discard)

            return rv
        else:
            # Hint: add `if tenant.accept_new_tasks` before `.create_task()`
            raise RuntimeError("task cannot be created at this time")

    def stop(self) -> None:
        self._running = False
        self._accept_new_tasks = False
        self._cluster.stop_watching()

    async def wait_stopped(self) -> None:
        if self._task_group is not None:
            tg = self._task_group
            self._task_group = None
            await tg.__aexit__(*sys.exc_info())

    def terminate_sys_pgcon(self) -> None:
        if self.__sys_pgcon is not None:
            self.__sys_pgcon.terminate()
            self.__sys_pgcon = None
        del self._sys_pgcon_waiter

    async def _pg_connect(self, dbname: str) -> pgcon.PGConnection:
        ha_serial = self._server._ha_master_serial
        if self.get_backend_runtime_params().has_create_database:
            pg_dbname = self.get_pg_dbname(dbname)
        else:
            pg_dbname = self.get_pg_dbname(defines.EDGEDB_SUPERUSER_DB)
        started_at = time.monotonic()
        try:
            rv = await pgcon.connect(
                self.get_pgaddr(), pg_dbname, self.get_backend_runtime_params()
            )
            if self._server._stmt_cache_size is not None:
                rv.set_stmt_cache_size(self._server._stmt_cache_size)
        except Exception:
            metrics.backend_connection_establishment_errors.inc()
            raise
        finally:
            metrics.backend_connection_establishment_latency.observe(
                time.monotonic() - started_at
            )
        if ha_serial == self._server._ha_master_serial:
            rv.set_tenant(self)
            if self._server._backend_adaptive_ha is not None:
                self._server._backend_adaptive_ha.on_pgcon_made(
                    dbname == defines.EDGEDB_SYSTEM_DB
                )
            metrics.total_backend_connections.inc()
            metrics.current_backend_connections.inc()
            return rv
        else:
            rv.terminate()
            raise ConnectionError("connected to outdated Postgres master")

    async def _pg_disconnect(self, conn: pgcon.PGConnection) -> None:
        metrics.current_backend_connections.dec()
        conn.terminate()

    @contextlib.asynccontextmanager
    async def use_sys_pgcon(self) -> AsyncGenerator[pgcon.PGConnection, None]:
        if not self._server._initing and not self._running:
            raise RuntimeError("EdgeDB server is not running.")

        await self._sys_pgcon_waiter.acquire()

        if not self._server._initing and not self._running:
            self._sys_pgcon_waiter.release()
            raise RuntimeError("EdgeDB server is not running.")

        if self.__sys_pgcon is None or not self.__sys_pgcon.is_healthy():
            conn, self.__sys_pgcon = self.__sys_pgcon, None
            if conn is not None:
                self._sys_pgcon_ready_evt.clear()
                conn.abort()
            # We depend on the reconnect on connection_lost() of __sys_pgcon
            await self._sys_pgcon_ready_evt.wait()
            if self.__sys_pgcon is None:
                self._sys_pgcon_waiter.release()
                raise RuntimeError("Cannot acquire pgcon to the system DB.")

        try:
            yield self.__sys_pgcon
        finally:
            self._sys_pgcon_waiter.release()

    def on_sys_pgcon_connection_lost(self, exc: Exception | None) -> None:
        try:
            if not self._running:
                # The tenant is shutting down, release all events so that
                # the waiters if any could continue and exit
                self._sys_pgcon_ready_evt.set()
                self._sys_pgcon_reconnect_evt.set()
                return

            logger.error(
                "Connection to the system database is "
                + ("closed." if exc is None else f"broken! Reason: {exc}")
            )
            self._server.set_pg_unavailable_msg(
                "Connection is lost, please check server log for the reason."
            )
            self.__sys_pgcon = None
            self._sys_pgcon_ready_evt.clear()
            if self._accept_new_tasks:
                self.create_task(
                    self._reconnect_sys_pgcon(), interruptable=True
                )
            self._server._on_pgcon_broken(True)
        except Exception:
            metrics.background_errors.inc(1.0, "on_sys_pgcon_connection_lost")
            raise

    async def _reconnect_sys_pgcon(self) -> None:
        try:
            conn = None
            while self._running:
                try:
                    conn = await self._pg_connect(defines.EDGEDB_SYSTEM_DB)
                    break
                except OSError:
                    # Keep retrying as far as:
                    #   1. This tenant is still running,
                    #   2. We still cannot connect to the Postgres cluster, or
                    pass
                except pgcon_errors.BackendError as e:
                    #   3. The Postgres cluster is still starting up, or the
                    #      HA failover is still in progress
                    if not (
                        e.code_is(pgcon_errors.ERROR_FEATURE_NOT_SUPPORTED)
                        or e.code_is(pgcon_errors.ERROR_CANNOT_CONNECT_NOW)
                        or e.code_is(
                            pgcon_errors.ERROR_READ_ONLY_SQL_TRANSACTION
                        )
                    ):
                        # TODO: ERROR_FEATURE_NOT_SUPPORTED should be removed
                        # once PostgreSQL supports SERIALIZABLE in hot standbys
                        raise

                if self._running:
                    try:
                        # Retry after INTERVAL seconds, unless the event is set
                        # and we can retry immediately after the event.
                        await asyncio.wait_for(
                            self._sys_pgcon_reconnect_evt.wait(),
                            defines.SYSTEM_DB_RECONNECT_INTERVAL,
                        )
                        # But the event can only skip one INTERVAL.
                        self._sys_pgcon_reconnect_evt.clear()
                    except asyncio.TimeoutError:
                        pass

            if not self._running:
                if conn is not None:
                    conn.abort()
                return

            assert conn is not None
            logger.info("Successfully reconnected to the system database.")
            self.__sys_pgcon = conn
            self.__sys_pgcon.mark_as_system_db()
            # This await is meant to be after mark_as_system_db() because we
            # need the pgcon to be able to trigger another reconnect if its
            # connection is lost during this await.
            await self.__sys_pgcon.listen_for_sysevent()
            self._server.set_pg_unavailable_msg(None)
        finally:
            self._sys_pgcon_ready_evt.set()

    def get_debug_info(self) -> dict[str, Any]:
        obj = dict(
            params=dict(
                tenant_id=self._tenant_id,
            ),
            pg_addr=self.get_pgaddr(),
        )

        return obj
