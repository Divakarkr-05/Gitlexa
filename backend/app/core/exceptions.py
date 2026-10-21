class GitlexaException(Exception):
    pass

class GitHubIntegrationError(GitlexaException):
    pass

class MCPToolExecutionError(GitlexaException):
    pass
