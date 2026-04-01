import { Link } from 'react-router';
import { StarRating } from './StarRating';
import { LikeButton } from './LikeButton';
import { MoviePlaceholderSVG } from '../assets/icons/MoviePlaceholderSVG';
import '../types/movies';

/**
 * @param {{ movie: MovieSearchResult }} props
 */
export function MovieCard({ movie, setCanContinue, likedMovies, setLikedMovies, linkToMovie })
{
    let genres = JSON.parse( JSON.stringify( movie.genres ) )
    if ( genres.length > 4 )
    {
        while ( genres.length > 4 )
        {
            genres.pop( );
        }
    }

    return (
        <Link
            to={linkToMovie ? `/movies/${movie.movieId}` : null}
            className="relative group flex-1 grow basis-0 min-w-90">
            <div
                className="rounded-md bg-willow-green-200 dark:bg-willow-green-900 p-2 shadow-m transition-[background-color,box-shadow,transform] duration-150 hover:shadow-l hover:bg-willow-green-300 dark:hover:bg-willow-green-800 min-h-fit"
            >
                <div
                    className="aspect-2/3 w-full rounded-md flex items-center justify-center"
                >
                    {
                        movie.tmdb?.poster_url ?
                        (
                            <img
                                src={movie.tmdb.poster_url}
                                alt={`${movie.tmdb ? movie.tmdb.title : movie.title} poster`}
                                className="w-full h-full rounded-md object-contain"
                            />
                        ) :
                        (
                            <MoviePlaceholderSVG className="fill-willow-green-300 dark:fill-willow-green-800 group-hover:fill-willow-green-400 dark:group-hover:fill-willow-green-700 transition-[fill] duration-150" />   
                        )
                    }
                </div>
                <div className="opacity-0 pointer-coarse:opacity-100 pointer-fine:group-hover:opacity-100 transition-opacity duration-150 bg-linear-to-t from-black/90 from-40% to-transparent w-full absolute bottom-0 left-0 h-[70%] z-10 rounded-br-md rounded-bl-md flex items-end p-4 text-white min-h-fit">
                    <div
                        className="h-[60%] w-full flex flex-col gap-1 bottom-0"
                    >
                        <div className="grow flex flex-col gap-2">
                            <h3
                                className="font-semibold text-xl"
                            >
                                {movie.tmdb ? movie.tmdb.title : movie.title}
                            </h3>
                            <span
                                className="text-md"
                            >
                                {movie.year}
                            </span>
                            {
                                movie.tmdb?.cast && (
                                    <span
                                        className="text-sm text-willow-green-200"
                                    >
                                        {movie.tmdb.cast[0].name} | {movie.tmdb.cast[1].name} | {movie.tmdb.cast[2].name}
                                    </span>
                                )
                            }
                            <span
                                className=""
                            >
                                {genres.join( " | " )}
                            </span>
                        </div>
                        <div className="flex flex-row justify-between">
                            <StarRating rating={movie.tmdb?.vote_average} />
                            <LikeButton movieId={movie.movieId} setCanContinue={setCanContinue} likedMovies={likedMovies} setLikedMovies={setLikedMovies} />
                        </div>
                    </div>
                </div>
            </div>
        </Link>
    )
}