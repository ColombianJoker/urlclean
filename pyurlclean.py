#!/usr/bin/env python3
#

# FROM: https://go.skimresources.com/?id=31959X896062&url=https%3A%2F%2Ftimex.com%2Fproducts%2Fdeepwater-arctic-40-5mm-stainless-steel-bracelet-watch-tw2y64500&sref=https%3A%2F%2Fwww.gearpatrol.com%2Fwatches%2Ftimex-deepwater-arctic%2F&xcust=%5Bcontent_id%7C981939%5Brefdomain%7Cwww.gearpatrol.com%5Bcontent_product_id%7C981962%5Bproduct_retailer_id%7CTimex
# TO: https://timex.com/products/deepwater-arctic-40-5mm-stainless-steel-bracelet-watch-tw2y64500

import argparse
from urllib.parse import parse_qs, unquote, urlparse


def clean_url(raw_url):
    """
    Extracts the destination URL from a tracker wrapper.
    """
    try:
        # Parse the wrapper URL
        parsed = urlparse(raw_url)

        # Extract query parameters into a dictionary
        query_params = parse_qs(parsed.query)

        # Look for common redirect keys (url, dest, link, target)
        # In the specific example, the key is 'url'
        target_keys = ["url", "dest", "link", "target"]

        for key in target_keys:
            if key in query_params:
                # parse_qs returns a list for each key; take the first item
                dirty_destination = query_params[key][0]
                # Unquote to turn %3A into : and %2F into /
                return unquote(dirty_destination)

        # If no redirect key found, return the original URL
        return raw_url
    except Exception as e:
        return f"Error processing URL: {e}"


def main():
    parser = argparse.ArgumentParser(
        description="Clean tracker/affiliate parameters from URLs."
    )
    parser.add_argument("urls", nargs="*", help="One or more URLs to clean")

    args = parser.parse_args()

    if not args.urls:
        print("No URLs provided. Usage: python cleaner.py <url1> <url2>")
        return

    for url in args.urls:
        print(clean_url(url))


if __name__ == "__main__":
    main()
