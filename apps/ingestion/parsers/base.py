from abc import ABC, abstractmethod

class BaseParser(ABC):
    """
    Standard interface contract that all file-format parsers must implement.
    Supports easy extensibility for new client formats.
    """
    
    @abstractmethod
    def parse(self, file_path) -> list[dict]:
        """
        Reads input stream/file path and returns a list of dictionaries,
        representing raw individual data records.
        """
        pass
        
    @abstractmethod
    def validate(self, row: dict) -> tuple[bool, list[str]]:
        """
        Runs format constraints and sanity rules against a raw row.
        Returns a tuple of (is_ok, error_messages).
        """
        pass
        
    @abstractmethod
    def normalize(self, row: dict) -> dict:
        """
        Converts source-specific values into the ActivityRecord schema.
        Returns a dictionary suitable for creating an ActivityRecord.
        """
        pass
        
    @abstractmethod
    def flag_suspicious(self, record_data: dict) -> str | None:
        """
        Runs heuristics to identify data quality anomalies.
        Returns a reason string or None.
        """
        pass
