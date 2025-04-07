""""""

# Synchronous version
class DbController:
    def __init__(self, url=None, namespace=None, database=None, user=None, password=None):
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

    def connect(self):
        """Connect to SurrealDB and authenticate"""
        from surrealdb import Surreal

        # Initialize connection
        self.db = Surreal(self.url)

        # Authenticate and set namespace/database
        signin_result = self.db.signin({
            "username": self.user,
            "password": self.password
        })

        # Use namespace and database
        self.db.use(self.namespace, self.database)

        return signin_result

    def query(self, statement, params=None):
        """
        Execute a SurrealQL query

        :param statement: SurrealQL statement
        :param params: Optional parameters for the query
        :return: Query results
        """
        if params is None:
            params = {}
        return self.db.query(statement, params)

    def update(self, record, data):
        """
        Update a record

        :param record: Record ID string (e.g., "table:id")
        :param data: Dictionary of data to update
        :return: Updated record
        """
        result = self.db.update(record, data)

        # Handle record ID conversion
        if isinstance(result, dict) and 'id' in result:
            _id = str(result.pop("id"))
            return {**result, 'id': _id}
        return result

    def create(self, table_name, data):
        """
        Create a new record

        :param table_name: Table name
        :param data: Dictionary of data for the new record
        :return: Created record
        """
        try:
            result = self.db.create(table_name, data)

            # Handle result formatting
            if isinstance(result, dict) and 'id' in result:
                _id = str(result.pop("id"))
                return {**result, 'id': _id}
            return result
        except Exception as e:
            print(f"ERROR creating record: {e}")
            return {}

    def select_many(self, table_name):
        """
        Select all records from a table

        :param table_name: Table name
        :return: List of records
        """
        result = self.db.select(table_name)

        # Process results
        if isinstance(result, list):
            for i, record in enumerate(result):
                if isinstance(record, dict) and 'id' in record:
                    _id = str(record.pop("id"))
                    result[i] = {**record, 'id': _id}

        return result

    def select(self, record):
        """
        Select a specific record

        :param record: Record ID string (e.g., "table:id")
        :return: Record data
        """
        result = self.db.select(record)

        # Handle record ID conversion
        if isinstance(result, dict) and 'id' in result:
            _id = str(result.pop("id"))
            return {**result, 'id': _id}
        return result

    def delete(self, record):
        """
        Delete a record

        :param record: Record ID string (e.g., "table:id")
        :return: Result of deletion
        """
        return self.db.delete(record)

    def close(self):
        """Close the connection (not needed with new API, but kept for compatibility)"""
        # The new API doesn't seem to have an explicit close method
        # This is kept for backwards compatibility
        pass


# Asynchronous version
class AsyncDbController:
    def __init__(self, url=None, namespace=None, database=None, user=None, password=None):
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

    async def connect(self):
        """Connect to SurrealDB and authenticate"""
        from surrealdb import AsyncSurreal

        # Initialize connection
        self.db = AsyncSurreal(self.url)

        # Authenticate and set namespace/database
        signin_result = self.db.signin({
            "username": self.user,
            "password": self.password
        })

        # Use namespace and database
        await self.db.use(self.namespace, self.database)

        return signin_result

    async def query(self, statement, params=None):
        """
        Execute a SurrealQL query

        :param statement: SurrealQL statement
        :param params: Optional parameters for the query
        :return: Query results
        """
        if params is None:
            params = {}
        return await self.db.query(statement, params)

    async def update(self, record, data):
        """
        Update a record

        :param record: Record ID string (e.g., "table:id")
        :param data: Dictionary of data to update
        :return: Updated record
        """
        result = await self.db.update(record, data)

        # Handle record ID conversion
        if isinstance(result, dict) and 'id' in result:
            _id = str(result.pop("id"))
            return {**result, 'id': _id}
        return result

    async def create(self, table_name, data):
        """
        Create a new record

        :param table_name: Table name
        :param data: Dictionary of data for the new record
        :return: Created record
        """
        try:
            result = await self.db.create(table_name, data)

            # Handle result formatting
            if isinstance(result, dict) and 'id' in result:
                _id = str(result.pop("id"))
                return {**result, 'id': _id}
            return result
        except Exception as e:
            print(f"ERROR creating record: {e}")
            return {}

    async def select_many(self, table_name):
        """
        Select all records from a table

        :param table_name: Table name
        :return: List of records
        """
        result = await self.db.select(table_name)

        # Process results
        if isinstance(result, list):
            for i, record in enumerate(result):
                if isinstance(record, dict) and 'id' in record:
                    _id = str(record.pop("id"))
                    result[i] = {**record, 'id': _id}

        return result

    async def select(self, record):
        """
        Select a specific record

        :param record: Record ID string (e.g., "table:id")
        :return: Record data
        """
        result = await self.db.select(record)

        # Handle record ID conversion
        if isinstance(result, dict) and 'id' in result:
            _id = str(result.pop("id"))
            return {**result, 'id': _id}
        return result

    async def delete(self, record):
        """
        Delete a record

        :param record: Record ID string (e.g., "table:id")
        :return: Result of deletion
        """
        return await self.db.delete(record)

    async def close(self):
        """Close the connection (not needed with new API, but kept for compatibility)"""
        # The new API doesn't seem to have an explicit close method
        # This is kept for backwards compatibility
        pass
