from flask import jsonify, current_app
from flask_jwt_extended import jwt_required, current_user
import sqlalchemy as sa

from app.extensions import db
from app import tmdb_service, movie_search_service
from app.models import RecommendationSet, CachedRecommendation
from app.recommendations import bp


def serialise_recommendation_movie(
    movie_id: int,
    score: float,
    tmdb_enrichment_available: bool
) -> dict:
    """
    Serialise a recommended movie into the response shape returned by the API.
    Parameters:
        movie_id (int):                   dataset movie id.
        score (float):                    recommendation score.
        tmdb_enrichment_available (bool): whether TMDB metadata enrichment can be attempted.
    """
    movie = movie_search_service.get_movie(movie_id) if movie_search_service and movie_search_service.is_ready else None

    if movie is None:
        return {
            "movieId": int(movie_id),
            "score": float(score),
            "title": None,
            "year": None,
            "genres": [],
            "tmdbId": None,
            "tmdb": None
        }

    tmdb = None
    if tmdb_enrichment_available and current_user.tmdb_api_key:
        tmdb = tmdb_service.get_cached_or_fetch_movie_metadata(
            movie_id=movie["movieId"],
            tmdb_id=movie["tmdbId"],
            api_key=current_user.tmdb_api_key
        )

    return {
        "movieId": int(movie["movieId"]),
        "score": float(score),
        "title": movie["title"],
        "year": movie["year"],
        "genres": movie["genres"],
        "tmdbId": movie["tmdbId"],
        "tmdb": tmdb
    }


def serialise_recommendation_set(
    recommendation_set: RecommendationSet,
    tmdb_enrichment_available: bool
) -> dict:
    """
    Serialise a cached recommendation set and its movies.
    Parameters:
        recommendation_set (RecommendationSet): recommendation set to serialise.
        tmdb_enrichment_available (bool):       whether TMDB metadata enrichment can be attempted.
    """
    cached_recommendations = db.session.scalars(
        sa.select(CachedRecommendation)
        .where(CachedRecommendation.user_set_id == recommendation_set.id)
        .order_by(CachedRecommendation.score.desc())
    ).all()

    movies = [
        serialise_recommendation_movie(
            movie_id=int(cached_recommendation.movie_id),
            score=float(cached_recommendation.score),
            tmdb_enrichment_available=tmdb_enrichment_available
        )
        for cached_recommendation in cached_recommendations
    ]

    return {
        "id": recommendation_set.id,
        "timestamp": recommendation_set.timestamp.isoformat() if recommendation_set.timestamp else None,
        "movies": movies
    }

@bp.route("/status", methods=["GET"])
@jwt_required()
def recommendation_status():
    recommender = current_app.extensions.get("recommender")

    if recommender is None:
        return jsonify({
            "error": "Recommender is not available."
        }), 503

    if not recommender.is_ready:
        return jsonify({
            "error": recommender.status_message or "Recommender is not ready."
        }), 503
    
    if recommender.is_generating:
        return jsonify({
            "running": recommender.is_generating,
            "started_at": recommender.generation_started_at
        }), 200
    
    return jsonify({
        "running": recommender.is_generating
    }), 200

@bp.route("/initialise", methods=["POST"])
@jwt_required()
def initialise_recommeder():
    """
    Initialise the recommender.
    """
    recommender = current_app.extensions["recommender"]
    recommender_status = current_app.extensions["recommender_status"]

    if recommender_status["is_ready"] and not recommender_status["needs_manual_initialisation"]:
        return jsonify({
            "error": "Recommender is already initialised."
        }), 409
    
    recommender.manual_initialise()
    current_app.extensions["recommender_status"] = recommender.get_status()
    recommender_status = recommender.get_status()

    if not recommender_status["is_ready"]:
        return jsonify({
            "error": "Failed to initialise the recommender",
            "recommender": recommender_status
        }), 500
    
    return jsonify({
        "message": "Recommender was successfully initialised.",
        "recommender": recommender_status
    }), 200

@bp.route("/create", methods=["POST"])
@jwt_required()
def create_recommendations():
    """
    Create a new recommendation set for the current user and return it.
    """
    recommender = current_app.extensions.get("recommender")

    if recommender is None:
        return jsonify({
            "error": "Recommender is not available."
        }), 503

    if not recommender.is_ready:
        return jsonify({
            "error": recommender.status_message or "Recommender is not ready."
        }), 503
    
    if recommender.is_generating:
        return jsonify({
            "error": "Recommender is already creating recommendations."
        }), 409

    tmdb_enrichment_available = bool(
        current_user.tmdb_api_key and current_user.tmdb_api_key_valid
    )

    try:
        recommendations = recommender.recommend(
            user=current_user,
            top_n=10,
            candidate_n=50,
            cache_result=True
        )
    except RuntimeError as e:
        return jsonify({
            "error": str(e)
        }), 503

    latest_recommendation_set = db.session.scalar(
        sa.select(RecommendationSet)
        .where(RecommendationSet.user == current_user)
        .order_by(RecommendationSet.timestamp.desc(), RecommendationSet.id.desc())
    )

    if latest_recommendation_set is None:
        return jsonify({
            "error": "Failed to create recommendation set."
        }), 500

    return jsonify({
        "recommendation_set": serialise_recommendation_set(
            latest_recommendation_set,
            tmdb_enrichment_available=tmdb_enrichment_available
        )
    }), 200


@bp.route("/latest", methods=["GET"])
@jwt_required()
def get_latest_recommendation_set():
    """
    Get the latest cached recommendation set for the current user.
    """
    latest_recommendation_set = db.session.scalar(
        sa.select(RecommendationSet)
        .where(RecommendationSet.user == current_user)
        .order_by(RecommendationSet.timestamp.desc(), RecommendationSet.id.desc())
    )

    if latest_recommendation_set is None:
        return jsonify({
            "recommendation_set": []
        }), 200

    tmdb_enrichment_available = bool(
        current_user.tmdb_api_key and current_user.tmdb_api_key_valid
    )

    return jsonify({
        "recommendation_set": serialise_recommendation_set(
            latest_recommendation_set,
            tmdb_enrichment_available=tmdb_enrichment_available
        )
    }), 200


@bp.route("/sets", methods=["GET"])
@jwt_required()
def get_recommendation_sets():
    """
    Get all cached recommendation sets for the current user.
    """
    recommendation_sets = db.session.scalars(
        sa.select(RecommendationSet)
        .where(RecommendationSet.user == current_user)
        .order_by(RecommendationSet.timestamp.desc(), RecommendationSet.id.desc())
    ).all()

    tmdb_enrichment_available = bool(
        current_user.tmdb_api_key and current_user.tmdb_api_key_valid
    )

    return jsonify({
        "recommendation_sets": [
            serialise_recommendation_set(
                recommendation_set,
                tmdb_enrichment_available=tmdb_enrichment_available
            )
            for recommendation_set in recommendation_sets
        ]
    }), 200