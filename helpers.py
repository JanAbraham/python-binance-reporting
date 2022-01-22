def API_weight_check(client):
    """verify current payload of Binance API and trigger cool-off

    if 85% of max payload has been reached
    sends as well a keepalive signal for the api connection
    Goal: avoid errors while downloading data from binance
    Return: the payload value after checking & cool-off
    TODO: read current max value for Payload from Binance config
    TODO: SAPI API seems to have threshold of 12000 => incorporate those (discovered during snapshot downloads)
    import time  # used for sleep / cool-off
    """
    logging.debug("check payload of API")
    # customizable variables
    api_payload_threshold = 0.75  # Threshold is max 75%
    api_payload_limit = {
        "x-mbx-used-weight": 1200 * api_payload_threshold,
        "x-mbx-used-weight-1m": 1200 * api_payload_threshold,
        "X-SAPI-USED-IP-WEIGHT-1M": 12000 * api_payload_threshold,
    }

    # internal variables
    int_loop_counter = 0
    api_header_used = ""

    # find out which of the headers is used in the API calls
    for api_header in api_payload_limit:
        if api_header in client.response.headers:
            api_header_used = api_header

    # loop as long as api payload is above threshold
    while (
        int(client.response.headers[api_header_used])
        > api_payload_limit[api_header_used]
    ):
        int_loop_counter = int_loop_counter + 1
        logging.warning(
            "API overused! Waiting "
            + str(int_loop_counter)
            + "min for API to cool-off."
        )
        logging.debug("Payload = " + str(client.response.headers[api_header_used]))
        time.sleep(int_loop_counter * 60)
        # make sure the api connection stays alive during the cool-off period
        try:
            logging.debug("   ... sending keepalive signal to exchange.")
            logging.debug("api_header used before keep alive ping: " + api_header_used)
            listenkey = client.stream_get_listen_key()
            client.stream_keepalive(listenkey)
            # find out which of the headers is used in the API calls
            # this might change after keep alive ping
            for api_header in api_payload_limit:
                if api_header in client.response.headers:
                    api_header_used = api_header
            logging.debug("api_header used after keep alive ping: " + api_header_used)
        except Exception as e:
            logging.warning("Error: " + str(e.code) + " (" + e.message + ")")

    logging.debug(
        "Check payload of API finished. Current Payload is "
        + str(client.response.headers[api_header_used])
    )
    return client.response.headers[api_header_used]


def API_close_connection(client):
    """close API connection of a given client

    to keep the environment lean and clean
    TODO add different connection types for futures etc.
    """

    logging.debug("closing API connection")
    try:
        client.stream_close(client.stream_get_listen_key())
    except Exception as e:
        logging.warning("Error: " + str(e.code) + " (" + e.message + ")")
    logging.debug("API connection closed (if no error has been reported before)")


def file_remove_blanks(filename):
    """read csv file and remove blank lines
    those blank lines are sometimes created when saving
    csv files under windows
    """
    logging.info("removing blank rows from " + filename)
    data = pd.read_csv(filename, skip_blank_lines=True, low_memory=False)
    data.dropna(how="all", inplace=True)
    data.to_csv(filename, header=True)
    logging.info("blank rows removed from " + filename)