import { MovieCard } from './MovieCard';
import '../types/movies';

/**
 * @param {{ movies: MovieSearchResult[] }} props
 */
export function MovieGrid({ movies, setCanContinue, likedMovies, setLikedMovies })
{
    return (
        <div
            className="grid grid-cols-[repeat(auto-fit,minmax(300px,1fr))] gap-10"
        >
            {
                movies.map( ( movie ) =>
                {
                    return (
                        <MovieCard
                            movie={movie}
                            setCanContinue={setCanContinue}
                            likedMovies={likedMovies}
                            setLikedMovies={setLikedMovies}
                            key={movie.movieId}
                        />
                    );
                } )
            }
        </div>
    );
}