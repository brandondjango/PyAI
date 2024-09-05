import os
import concurrent.futures

from flask import Flask, request, jsonify, Response

from src.data_scraper.match_fetcher import MatchFetcher
from src.data_scraper.match_scraper import MatchScraper
from datetime import datetime

from src.database_connector.postgres_connector import PostgresConnector

app = Flask(__name__)

def scrape_individual_match(match_id, postgres_connector):
    MatchScraper.scrape_match(match_id, postgres_connector=postgres_connector)

def scrape_matches_in_threads(match_ids):
    postgres_connector = PostgresConnector()
    postgres_connector.open_connection_cursor("premier_league_stats")

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        # Submit tasks to scrape each URL and write to the database
        futures = [executor.submit(scrape_individual_match, match_id, postgres_connector) for match_id in match_ids]

    # Wait for all tasks to complete
    for future in concurrent.futures.as_completed(futures):
        future.result()


@app.route('/scrape_season', methods=['POST'])
def scrape_season():
    data = request.json


    comp_id = data.get("competition_id")
    season = data.get("season")
    match_ids = MatchFetcher.fetch_matches_from_season_scores_and_fixtures_page(comp_id, season)

    scrape_matches_in_threads(match_ids)
    response = {
        "Start": "ok"
    }
    return jsonify(response), 200


@app.route('/scrape_match', methods=['POST'])
def scrape_match():
    data = request.json

    if data.get("match_id") is None:
        response = {
            'status': 'Failed',
            'message': "Match Id not provided: "
        }
        return jsonify(response), 500

    match_id = data.get("match_id")

    MatchScraper.scrape_match(match_id)

    # Process the data as needed
    response = {
        'status': 'success',
        'message': "Scraped match with id: " + match_id
    }
    return jsonify(response), 200

@app.route('/db_setup', methods=['POST'])
def db_setup_endpoint():
    data = request.json
    db_pass = data.get('db_pass')

    os.environ['DB_PASS'] = db_pass

    # Process the data as needed
    response = {
        'status': 'success',
        'data_received': os.environ['DB_PASS']
    }
    return jsonify(response), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)