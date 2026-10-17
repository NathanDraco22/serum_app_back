import uuid


class UuidTool:
    @staticmethod
    def generate_uuid() -> str:
        return str(uuid.uuid4())
