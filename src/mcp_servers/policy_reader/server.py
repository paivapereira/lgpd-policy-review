"""policy-reader MCP server.

Exposes the versioned LGPD Data Protection Policy as queryable resource
and as compliance-evaluation tool. See docs/specs/policy-reader/canonical.md
for the contract.
"""
from fastmcp import FastMCP

mcp = FastMCP("policy-reader")


if __name__ == "__main__":
    mcp.run()