/**
 * @typedef {Object} TmdbMovieMetadata
 * @property {number} tmdb_id
 * @property {string} title
 * @property {string} overview
 * @property {string} poster_path
 * @property {string} poster_url
 * @property {string} backdrop_path
 * @property {string} backdrop_url
 * @property {string} release_date
 * @property {number} vote_average
 * @property {MovieSearchResultCast[]} cast
 * @property {number} runtime 
 */

/**
 * @typedef {Object} MovieSearchResult
 * @property {number} movieId
 * @property {string} title
 * @property {number | null} year
 * @property {string[]} genres
 * @property {number | null} tmdbId
 * @property {TmdbMovieMetadata | null} tmdb
 */

/**
 * @typedef {Object} MovieSearchResultCast
 * @property {number} id
 * @property {string} name
 * @property {string} character
 * @property {string} profile_path
 * @property {string} profile_url
 * @property {number} order
 */

/**
 * @typedef {Object} MovieSearchResponse
 * @property {MovieSearchResult[]} results
 * @property {string} query
 * @property {boolean} tmdb_enrichment_available
 */