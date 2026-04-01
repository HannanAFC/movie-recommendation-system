/**
 * @typedef {Object} UserResponse
 * @property {User} user
 */

/**
 * @typedef {Object} User
 * @property {boolean} dataset_selected
 * @property {string} email
 * @property {MovieSearchStatus} movie_search
 * @property {boolean} needs_to_select_movies
 * @property {RecommenderStatus} recommender
 * @property {TMDBAPIKeyStatus} tmdb
 * @property {string} username
 */

/**
 * @typedef {Object} MovieSearchStatus
 * @property {boolean} is_ready
 * @property {string} status_message
 */

/**
 * @typedef {Object} RecommenderStatus
 * @property {boolean} is_ready
 * @property {boolean} needs_manual_initialisation
 * @property {string} status_message
 */

/**
 * @typedef {Object} TMDBAPIKeyStatus
 * @property {string} api_key_last_validated_at
 * @property {boolean} api_key_set
 * @property {boolean} api_key_valid
 */