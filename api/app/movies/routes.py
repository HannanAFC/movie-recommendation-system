from flask import request, jsonify
import sqlalchemy as sa
from flask_jwt_extended import jwt_required, current_user
from app import dataset_manager, tmdb_service, movie_search_service
from app.movies import bp
from app.extensions import db
from app.utils import build_movie_id_lookup
from app.models import LikedMovie

@bp.route("/search", methods=["GET"])
@jwt_required()
def search_movies():
    query = (request.args.get("q") or "").strip()
    limit = int(request.args.get("limit", 10))

    if not query:
        return jsonify({"error": "Search query required."}), 422

    if not dataset_manager.dataset_exists():
        return jsonify({"error": "No dataset is currently installed."}), 409

    if movie_search_service is None or not movie_search_service.is_ready:
        return jsonify({"error": "Movie search is not ready."}), 503

    tmdb_enrichment_available = bool(
        current_user.tmdb_api_key and current_user.tmdb_api_key_valid
    )

    results = movie_search_service.search_and_enrich(
        query=query,
        limit=limit,
        api_key=current_user.tmdb_api_key if tmdb_enrichment_available else None,
        tmdb_service=tmdb_service
    )

    return jsonify({
        "results": results,
        "query": query,
        "tmdb_enrichment_available": tmdb_enrichment_available
    }), 200

@bp.route("/liked", methods=["GET"])
@jwt_required()
def get_liked_movies():
    liked_movies = current_user.get_liked_movies()
    
    liked_movie_ids = [
        liked_movie.movie_id
        for liked_movie in liked_movies
    ]

    return jsonify({
        "liked_movie_ids": liked_movie_ids
    })

@bp.route("/like/<movie_id>", methods=["POST", "DELETE"])
@jwt_required()
def like_movie(movie_id):
    if not movie_id:
        return jsonify({
            "error": "Please provide a movie ID."
        }), 422

    try:
        movie_id = int(movie_id)
    except ValueError:
        return jsonify({
            "error": "Invalid movie ID."
        }), 422

    if movie_search_service is None or not movie_search_service.is_ready:
        return jsonify({
            "error": "Movie search service is not ready."
        }), 503

    if not movie_search_service.movie_exists(movie_id):
        return jsonify({
            "error": "Movie is not in the current dataset."
        }), 409

    already_liked = db.session.scalar(
        sa.select(LikedMovie).where(
            LikedMovie.movie_id_lookup == build_movie_id_lookup(movie_id),
            LikedMovie.rating_author == current_user,
        )
    )

    if request.method == "POST":
        if already_liked is not None:
            return jsonify({
                "error": "Movie already liked."
            }), 422

        liked_movie = LikedMovie(
            movie_id=movie_id,
            movie_id_lookup=build_movie_id_lookup(movie_id),
            rating_author=current_user
        )

        db.session.add(liked_movie)
        db.session.commit()

        needs_to_select_movies = (
            len(current_user.get_user_ratings()) == 0 and
            len(current_user.get_liked_movies()) < 5
        )

        return jsonify({
            "message": "Movie has been liked successfully.",
            "needs_to_select_movies": needs_to_select_movies
        }), 200

    else:
        if already_liked is None:
            return jsonify({
                "error": "Movie is not liked."
            }), 422

        db.session.delete(already_liked)
        db.session.commit()

        needs_to_select_movies = (
            len(current_user.get_user_ratings()) == 0 and
            len(current_user.get_liked_movies()) < 5
        )

        return jsonify({
            "message": "Movie has been unliked successfully.",
            "needs_to_select_movies": needs_to_select_movies
        }), 200

@bp.route("/clear-cache/<movie_id>", methods=["DELETE"])
@jwt_required()
def clear_movie_cache(movie_id):
    if movie_id == "all":
        removed = tmdb_service.clear_cache()
        return jsonify({
            "message": f"Removed {removed} {"movies" if removed == 1 else "movie"} from cache."
        })
    
    try:
        int(movie_id)
    except ValueError:
        return jsonify({
            "error": "Not a valid movie ID."
        }), 422
    
    removed = tmdb_service.clear_cached_movie_metadata(movie_id)

    return jsonify({
        "message": f"Removed {removed} {"movies" if removed == 1 else "movie"} from cache."
    }), 200