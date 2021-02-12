# BOKEH

- Embed a bokeh app (with tornado control) into this python package
- we can mix the tornado loop with asyncio (1 proc only)

# CURRENTLY
- keep only one user (config at startup)
- keep one simple app, with a way to connect it with aiobinance async tasks for data updates.
- keep tornado as server, tightly integrating with aiohttp might be overly tricky.
