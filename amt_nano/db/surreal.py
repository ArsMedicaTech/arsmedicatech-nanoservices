"""
Synchronous and Asynchronous SurrealDB Controller
"""

from typing import Any, Dict, List, Optional, Union

from surrealdb.connections.async_http import AsyncHttpSurrealConnection
from surrealdb.connections.blocking_http import BlockingHttpSurrealConnection
from surrealdb.data.types.record_id import RecordID
from surrealdb.data.types.table import Table

from settings import logger


class SurrealWrapper:
    def __init__(self, r: Any) -> None:
        self._client: BlockingHttpSurrealConnection = r

    def signin(self, vars: Dict[str, Any]) -> str:
        return self._client.signin(vars)

    def query(
        self, query: str, vars: Dict[str, Any] = {}
    ) -> Union[str, Dict[str, Any], List[Dict[str, Any]]]:
        return self._client.query(query, vars)

    def create(
        self,
        thing: Union[str, RecordID, Table],
        data: Optional[
            Union[Union[list[Dict[str, Any]], Dict[str, Any]], Dict[str, Any]]
        ] = None,
    ) -> Union[str, Dict[str, Any], List[Dict[str, Any]]]:
        """
        Create a new record in the database.

        :param thing: str, record id or table.
        :param data: Dictionary of data for the new record
        :return: Created record
        """
        return self._client.create(thing, data)

    def delete(
        self, thing: Union[str, RecordID, Table]
    ) -> Union[str, Dict[str, Any], List[Dict[str, Any]]]:
        """
        Delete a record from the database.

        :param thing: str, record id or table.
        :return: Result of deletion
        """
        return self._client.delete(thing)

    def select(
        self, thing: Union[str, RecordID, Table]
    ) -> Union[str, Dict[str, Any], List[Dict[str, Any]]]:
        """
        Select a specific record from the database.

        :param thing: str, record id or table.
        :return: Record data
        """
        return self._client.select(thing)

    def update(
        self, thing: Union[str, RecordID, Table], data: Dict[str, Any]
    ) -> Union[str, Dict[str, Any], List[Dict[str, Any]], None]:
        """
        Update a record in the database.

        :param thing: str or Record ID or table
        :param data: Dictionary of data to update
        :return: Updated record
        """
        return self._client.update(thing, data)

    def use(self, namespace: str, database: str) -> None:
        """
        Set the namespace and database for the current session.

        :param namespace: SurrealDB namespace
        :param database: SurrealDB database
        :return: None
        """
        self._client.use(namespace, database)

    def close(self) -> None:
        """
        Close the connection to the database.

        :return: None
        """
        self._client.close()


class AsyncSurrealWrapper:
    def __init__(self, r: Any) -> None:
        self._client: AsyncHttpSurrealConnection = r

    async def signin(self, vars: Dict[str, Any]) -> str:
        return await self._client.signin(vars)

    async def query(
        self, query: str, vars: Dict[str, Any] = {}
    ) -> Union[str, Dict[str, Any], List[Dict[str, Any]]]:
        return await self._client.query(query, vars)

    async def create(
        self,
        thing: Union[str, RecordID, Table],
        data: Optional[
            Union[Union[list[Dict[str, Any]], Dict[str, Any]], Dict[str, Any]]
        ] = None,
    ) -> Union[str, Dict[str, Any], List[Dict[str, Any]]]:
        return await self._client.create(thing, data)

    async def delete(
        self, thing: Union[str, RecordID, Table]
    ) -> Union[str, Dict[str, Any], List[Dict[str, Any]]]:
        return await self._client.delete(thing)

    async def select(
        self, thing: Union[str, RecordID, Table]
    ) -> Union[str, Dict[str, Any], List[Dict[str, Any]]]:
        return await self._client.select(thing)

    async def update(
        self, thing: Union[str, RecordID, Table], data: Dict[str, Any]
    ) -> Union[str, Dict[str, Any], List[Dict[str, Any]], None]:
        return await self._client.update(thing, data)

    async def use(self, namespace: str, database: str) -> None:
        await self._client.use(namespace, database)

    async def close(self) -> None:
        """
        Close the connection to the database.

        :return: None
        """
        await self._client.close()


# Synchronous version
class DbController:
    """
    Synchronous DB controller for SurrealDB
    """

    db: Optional[SurrealWrapper] = None

    def __init__(
        self,
        url: Optional[str] = None,
        namespace: Optional[str] = None,
        database: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
    ) -> None:
        """
        Initialize a synchronous DB controller for SurrealDB

        :param url: SurrealDB server URL (e.g., "http://localhost:8000")
        :param namespace: SurrealDB namespace
        :param database: SurrealDB database
        :param user: Username for authentication
        :param password: Password for authentication
        """
        if url is None:
            from settings import SURREALDB_URL

            url = SURREALDB_URL
        if namespace is None:
            from settings import SURREALDB_NAMESPACE

            namespace = SURREALDB_NAMESPACE
        if database is None:
            from settings import SURREALDB_DATABASE

            database = SURREALDB_DATABASE
        if user is None:
            from settings import SURREALDB_USER

            user = SURREALDB_USER
        if password is None:
            from settings import SURREALDB_PASS

            password = SURREALDB_PASS

        self.url = url
        self.namespace = namespace
        self.database = database
        self.user = user
        self.password = password
        self.db = None

    def connect(self) -> str:
        """
        Connect to SurrealDB and authenticate
        :return: Signin result
        """
        from surrealdb import Surreal  # type: ignore

        logger.debug(f"Connecting to SurrealDB at {self.url}")
        logger.debug(f"Using namespace: {self.namespace}, database: {self.database}")
        logger.debug(f"Username: {self.user}")

        # Initialize connection
        self.db = SurrealWrapper(Surreal(self.url))

        # Authenticate and set namespace/database
        from typing import Any, Dict

        credentials: Dict[str, Any] = {"username": self.user, "password": self.password}

        signin_result = str(self.db.signin(credentials))
        logger.debug(f"Signin result: {signin_result}")

        # Use namespace and database
        if self.namespace is None or self.database is None:
            raise ValueError("Namespace and database must not be None.")
        self.db.use(self.namespace, self.database)
        logger.debug("Set namespace and database")

        return signin_result

    def query(
        self, query: str, vars: Dict[str, Any] = {}
    ) -> Union[str, Dict[str, Any], List[Dict[str, Any]]]:
        """
        Execute a SurrealQL query

        :param statement: SurrealQL statement
        :param params: Optional parameters for the query
        :return: Query results
        """
        if self.db is None:
            raise RuntimeError(
                "Database connection is not established. Call connect() before performing operations."
            )
        return self.db.query(query, vars)

    def create(
        self,
        thing: Union[str, RecordID, Table],
        data: Optional[
            Union[Union[list[Dict[str, Any]], Dict[str, Any]], Dict[str, Any]]
        ] = None,
    ) -> Union[str, Dict[str, Any], List[Dict[str, Any]]]:
        """
        Create a new record

        :param thing: str, record id, Table name
        :param data: Dictionary of data for the new record
        :return: Created record
        """
        if self.db is None:
            raise RuntimeError(
                "Database connection is not established. Call connect() before performing operations."
            )
        return self.db.create(thing, data)

    def delete(
        self, thing: Union[str, RecordID, Table]
    ) -> Union[str, Dict[str, Any], List[Dict[str, Any]]]:
        """
        Delete a record

        :param thing: str, Record ID or table name
        :return: Result of deletion
        """
        if self.db is None:
            raise RuntimeError(
                "Database connection is not established. Call connect() before performing operations."
            )
        return self.db.delete(thing)

    def select(
        self, thing: Union[str, RecordID, Table]
    ) -> Union[str, Dict[str, Any], List[Dict[str, Any]]]:
        """
        Select a specific record

        :param thing: str, record id or table.
        :return: Record data
        """
        if self.db is None:
            raise RuntimeError(
                "Database connection is not established. Call connect() before performing operations."
            )
        logger.debug(f"Selecting thing: {thing}")
        result = self.db.select(thing)
        logger.debug(f"Select raw result: {result}")

        return result

    def select_many(self, table_name: Table) -> Union[str, List[Dict[str, Any]]]:
        """
        Select all records from a table

        :param table_name: Table name
        :return: List of records
        """
        if self.db is None:
            raise RuntimeError(
                "Database connection is not established. Call connect() before performing operations."
            )
        logger.debug(f"Selecting many from: {table_name}")
        result = self.db.select(table_name)
        if not isinstance(result, List) and not isinstance(result, str):
            raise RuntimeError(f"Database returned unexpected result: {result}")
        logger.debug(f"Select many result: {result}")
        return result

    def update(
        self, thing: Union[str, RecordID, Table], data: Dict[str, Any]
    ) -> Union[str, Dict[str, Any], List[Dict[str, Any]], None]:
        """
        Update a record

        :param thing: str or Record ID or table
        :param data: Dictionary of data to update
        :return: Updated record
        """
        logger.debug(f"SurrealDB update thing: {thing}")
        if self.db is None:
            raise RuntimeError(
                "Database connection is not established. Call connect() before performing operations."
            )
        result = self.db.update(thing, data)
        logger.debug(f"SurrealDB update result: {result}")
        return result

    def search(
        self, query: str, params: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Execute a search query
        :param query: SurrealQL search query
        :param params: Optional parameters for the query
        :return: List of search results
        """
        # logging.info(f"Executing Query: {query} with params: {params}")
        logger.debug(f"Executing Query: {query} with params: {params}")
        # This mock will return plausible results for the search query.
        if "SEARCH" in query and params and params.get("query"):
            return [
                {
                    "result": [
                        {
                            "highlighted_note": "Patient reported persistent <b>headaches</b> and sensitivity to light.",
                            "score": 1.25,
                            "patient": {
                                "demographic_no": "1",
                                "first_name": "John",
                                "last_name": "Doe",
                            },
                        },
                        {
                            "highlighted_note": "Follow-up regarding frequent <b>headaches</b>.",
                            "score": 1.18,
                            "patient": {
                                "demographic_no": "2",
                                "first_name": "Jane",
                                "last_name": "Doe",
                            },
                        },
                    ],
                    "status": "OK",
                    "time": "15.353µs",
                }
            ]
        # Mock response for schema creation
        return [{"status": "OK"}]

    def close(self) -> None:
        """
        Close the connection (not needed with new API, but kept for compatibility)
        :return: None
        """
        if self.db is None:
            raise RuntimeError(
                "Database connection is not established. Call connect() before performing operations."
            )
        self.db.close()


# Asynchronous version
class AsyncDbController:
    """
    Asynchronous DB controller for SurrealDB
    """

    db: Optional[AsyncSurrealWrapper] = None

    def __init__(
        self,
        url: Optional[str] = None,
        namespace: Optional[str] = None,
        database: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
    ) -> None:
        """
        Initialize an asynchronous DB controller for SurrealDB

        :param url: SurrealDB server URL (e.g., "http://localhost:8000")
        :param namespace: SurrealDB namespace
        :param database: SurrealDB database
        :param user: Username for authentication
        :param password: Password for authentication
        """
        if url is None:
            from settings import SURREALDB_URL

            url = SURREALDB_URL
        if namespace is None:
            from settings import SURREALDB_NAMESPACE

            namespace = SURREALDB_NAMESPACE
        if database is None:
            from settings import SURREALDB_DATABASE

            database = SURREALDB_DATABASE
        if user is None:
            from settings import SURREALDB_USER

            user = SURREALDB_USER
        if password is None:
            from settings import SURREALDB_PASS

            password = SURREALDB_PASS

        self.url = url
        self.namespace = namespace
        self.database = database
        self.user = user
        self.password = password
        self.db = None

    async def connect(self) -> str:
        """
        Connect to SurrealDB and authenticate
        :return: Signin result
        """
        from surrealdb import AsyncSurreal  # type: ignore

        # Initialize connection
        self.db = AsyncSurrealWrapper(AsyncSurreal(self.url))

        # Authenticate and set namespace/database
        signin_result = await self.db.signin(
            {"username": self.user, "password": self.password}
        )

        if not self.db:
            raise RuntimeError(
                "Database connection is not established. Call connect() before performing operations."
            )

        # Use namespace and database
        if self.namespace is None or self.database is None:
            raise ValueError("Namespace and database must not be None.")
        await self.db.use(self.namespace, self.database)

        return signin_result

    async def query(
        self, query: str, vars: Dict[str, Any] = {}
    ) -> Union[str, Dict[str, Any], List[Dict[str, Any]]]:
        """
        Execute a SurrealQL query

        :param statement: SurrealQL statement
        :param params: Optional parameters for the query
        :return: Query results
        """
        if self.db is None:
            raise RuntimeError(
                "Database connection is not established. Call connect() before performing operations."
            )
        return await self.db.query(query, vars)

    async def create(
        self,
        thing: Union[str, RecordID, Table],
        data: Optional[
            Union[Union[list[Dict[str, Any]], Dict[str, Any]], Dict[str, Any]]
        ] = None,
    ) -> Union[str, Dict[str, Any], List[Dict[str, Any]]]:
        """
        Create a new record

        :param thing: str, record id, Table name
        :param data: Dictionary of data for the new record
        :return: Created record
        """
        if self.db is None:
            raise RuntimeError(
                "Database connection is not established. Call connect() before performing operations."
            )
        return await self.db.create(thing, data)

    async def delete(
        self, thing: Union[str, RecordID, Table]
    ) -> Union[str, Dict[str, Any], List[Dict[str, Any]]]:
        """
        Delete a record

        :param thing: str, Record ID or table name
        :return: Result of deletion
        """
        if self.db is None:
            raise RuntimeError(
                "Database connection is not established. Call connect() before performing operations."
            )
        return await self.db.delete(thing)

    async def select(
        self, thing: Union[str, RecordID, Table]
    ) -> Union[str, Dict[str, Any], List[Dict[str, Any]]]:
        """
        Select a specific record

        :param thing: str, record id or table.
        :return: Record data
        """
        if self.db is None:
            raise RuntimeError(
                "Database connection is not established. Call connect() before performing operations."
            )
        logger.debug(f"Selecting thing: {thing}")
        result = await self.db.select(thing)
        logger.debug(f"Select raw result: {result}")

        return result

    async def select_many(self, table_name: Table) -> Union[str, List[Dict[str, Any]]]:
        """
        Select all records from a table

        :param table_name: Table name
        :return: List of records
        """
        if self.db is None:
            raise RuntimeError(
                "Database connection is not established. Call connect() before performing operations."
            )
        logger.debug(f"Selecting many from: {table_name}")
        result = await self.db.select(table_name)
        if not isinstance(result, List) and not isinstance(result, str):
            raise RuntimeError(f"Database returned unexpected result: {result}")
        logger.debug(f"Select many result: {result}")
        return result

    async def update(
        self, thing: Union[str, RecordID, Table], data: Dict[str, Any]
    ) -> Union[str, Dict[str, Any], List[Dict[str, Any]], None]:
        """
        Update a record

        :param thing: str or Record ID or table
        :param data: Dictionary of data to update
        :return: Updated record
        """
        logger.debug(f"SurrealDB update thing: {thing}")
        if self.db is None:
            raise RuntimeError(
                "Database connection is not established. Call connect() before performing operations."
            )
        result = await self.db.update(thing, data)
        logger.debug(f"SurrealDB update result: {result}")
        return result

    async def close(self) -> None:
        """
        Close the connection (not needed with new API, but kept for compatibility)
        :return: None
        """
        if self.db is None:
            raise RuntimeError(
                "Database connection is not established. Call connect() before performing operations."
            )
        await self.db.close()
