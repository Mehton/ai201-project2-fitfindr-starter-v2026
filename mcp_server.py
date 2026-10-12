"""
Your MCP server. ← UNIT 4, MILESTONE 1

Right now your tools only exist inside your own program. Nothing else can reach
them. MCP is an agreed shape you wrap a tool in so that anything speaking the
same protocol can call it — your agent today, a different agent tomorrow,
someone else's app after that.

**You're moving one tool. Not three.** The point is to see the seam.
`search_listings` is the one to move: it doesn't call the model, so nothing is
slow and nothing changes between runs while you're learning the shape.

    python mcp_server.py        starts the server (it will just sit there — that's right)
    python mcp_client.py        asks the server what it offers

─────────────────────────────────────────────────────────────────────────────
TODO — register one tool.

Uncomment the block below and fill it in. Three things matter:

  1. **search_listings.** Exactly what your agent will ask for.

  2. **The description.** This is the part that isn't code and matters most.
     Write it before you look at the example. You are not writing it for your
     agent — you're writing it for an agent someone else builds, that will
     never see your implementation. That isn't hypothetical; it's what every
     MCP server on the registry is.

     Two things to get right: name units and types ("price" is ambiguous,
     "max_price, in whole dollars" isn't), and state the empty case. Last unit
     the empty case was on your spec sheet for your loop's benefit. Here it's
     part of a published contract.

  3. **The typed inputs.** These come straight from your Tool Inventory. If the
     types here don't match your README, one of the two is wrong — fix it.

Then point your agent at it. In `run_agent()`, swap the direct call:

    results = search_listings(description, size, max_price)

for the MCP one:

    from mcp_client import call_tool
    results = call_tool("search_listings", {
        "description": description,
        "size": size,
        "max_price": max_price,
    })

**What comes back should not change.** If it does, that difference is your
first clue about what your tool was really returning before.

🛑 Stop rule: if this isn't connecting after 40 minutes, stop. Keep your direct
call, and write down in your README exactly where it broke — the error text and
the last thing that worked. Then carry on to Milestone 2. Everything after this
works with a direct call, and **a documented failure earns the point in full.**
─────────────────────────────────────────────────────────────────────────────
"""

from mcp.server.fastmcp import FastMCP

from tools import search_listings as _search_listings_impl  # noqa: F401 — you'll use this below
from tools import create_fit_card as _create_fit_card_impl
from generate import ModelUnavailable
from mcp.server.fastmcp.exceptions import ToolError

# log_level="WARNING" keeps the server from printing an INFO line for every
# request. Without it your terminal fills with "Processing request of type
# CallToolRequest" and the output you actually care about scrolls away.
mcp = FastMCP("fitfindr", log_level="WARNING")


# ── Registered MCP tool ───────────────────────────────────────────────────────
@mcp.tool()
def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    
    """
      Search the listings data for items matching a description, and optionally a
      size and a price ceiling.
  
      This is the tool that doesn't call the model, which makes it the easiest one
      to test and the one to move onto MCP in unit 4.
  
      Args:
          description: keywords describing what the user wants
                        (e.g. "vintage graphic tee").
          size:         a size string to filter by, or None to skip size filtering.
                        Match case-insensitively — "M" should match "S/M".
  
                        ⚠️ Read the sizes in the data before you reach for a plain
                        substring test. `"s" in "us 9"` is True, and so is
                        `"l" in "xl"`. A filter that returns shoes when someone
                        asked for a small top reads like a broken search, and it
                        will quietly cost you in unit 4 when you test criterion 1.
                        What counts as a size match is part of your spec — decide
                        it and write it into your Tool Inventory.
          max_price:   maximum price, inclusive, or None to skip price filtering.
  
      Returns:
          A list of matching listing dicts, best match first.
          **Returns an empty list when nothing matches — an empty list, not None,
          and not an exception.** Your loop branches on this.
  
      Each listing dict has these fields:
          id, title, description, category, style_tags (list), size,
          condition, price (float), colors (list), brand (str or None), platform

    """

    return _search_listings_impl(description, size, max_price)
# ──────────────────────────────────────────────────────────────────────────────
#
# Two notes on the block above.
#
# The registered name is the *function* name — so the block above registers
# "search_listings", which is exactly what call_tool("search_listings", ...)
# asks for. That is also why the import at the top of this file brings the real
# implementation in under an alias: without it, the registered function and the
# one it calls would be the same name, and the tool would call itself.
#
# FastMCP builds the input schema from your type hints, which is why the hints
# are not optional here. `description: str` becomes a required string;
# `max_price: float | None = None` becomes an optional number. Getting these
# wrong is the most common reason a call is rejected.


# ── Second registered MCP tool ────────────────────────────────────────────────
@mcp.tool()
def create_fit_card(outfit: str, new_item: dict) -> str:
    """Write a short, post-ready social caption (2-4 sentences) for a
    second-hand clothing find and the outfit it is styled in. Calls a
    language model, so the wording differs between calls.

    Inputs:
      outfit (string, required): the outfit description to caption, in
        plain text, e.g. "baggy dark-wash jeans, chunky white sneakers".
        Usually the output of an outfit-suggestion step.
      new_item (object, required): the listing being captioned. Only three
        fields are read: title (string), price (number, US dollars), and
        platform (string, e.g. "depop"). Any other fields are ignored, so a
        listing object returned by search_listings can be passed as-is.
        A missing title or platform falls back to generic wording; a
        missing or non-numeric price is written as "unknown".

    Returns:
      A non-empty string: the caption, mentioning the item title, its exact
      price (e.g. "$18"), and the platform.

    When the outfit is empty:
      If outfit is "" or only whitespace, no model call is made. It returns
      a fixed non-empty string naming the item, price, and platform, and
      asking for an outfit suggestion. Never an empty string or null.

    When the model can't be reached (bad API key, no network):
      Fails with a tool error whose message starts with "MODEL_UNAVAILABLE:".
      It does not return an empty string. Retrying will not help until the
      server's API key or network is fixed.
    """
    try:
        return _create_fit_card_impl(outfit, new_item)
    except ModelUnavailable as exc:
        raise ToolError(f"MODEL_UNAVAILABLE: {exc}") from exc
# ──────────────────────────────────────────────────────────────────────────────


if __name__ == "__main__":
    mcp.run()
