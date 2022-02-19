import logging

# Create a custom logger
server_logger = logging.getLogger("server")
server_logger.setLevel(logging.DEBUG)

# Create handlers
c_handler = logging.StreamHandler()

# Create formatters and add it to handlers
c_format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
c_handler.setFormatter(c_format)

# Add handlers to the logger
server_logger.addHandler(c_handler)


# Create a custom logger
fetchers_logger = logging.getLogger("fetchers")
fetchers_logger.setLevel(logging.DEBUG)

# Create handlers
c_handler = logging.StreamHandler()

# Create formatters and add it to handlers
c_format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
c_handler.setFormatter(c_format)

# Add handlers to the logger
fetchers_logger.addHandler(c_handler)


# Create a custom logger
update_cache_logger = logging.getLogger("update_cache")
update_cache_logger.setLevel(logging.DEBUG)

# Create handlers
c_handler = logging.StreamHandler()

# Create formatters and add it to handlers
c_format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
c_handler.setFormatter(c_format)

# Add handlers to the logger
update_cache_logger.addHandler(c_handler)
