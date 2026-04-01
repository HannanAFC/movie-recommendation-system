import { useState } from 'react';
import axios from 'axios';
import { useParams } from 'react-router';
import { BasicHeader } from '../components/BasicHeader';
import { useEffect } from 'react';
import '../types/movies'
import { formatDateFull } from '../utils/date';
import { formatRuntime } from '../utils/time'
import { StarRating } from '../components/StarRating';
import { LikeButton } from '../components/LikeButton';

export function MoviePage({ user, likedMovies, setLikedMovies })
{
    const { movieId } = useParams( );
    /** @type {[MovieSearchResult, React.Dispatch<React.SetStateAction<MovieSearchResult>>]} */
    const [ movie, setMovie ] = useState( null );
    const [ movieError, setMovieError ] = useState( null );
    const [ genres, setGenres ] = useState([ ]);

    useEffect( ( ) =>
    {
        async function fetchMovieData( )
        {
            const response = await axios.get( `/api/movies/${movieId}` )
            .catch( ( error ) =>
            {
                if ( error.response.status === 500 )
                {
                    setMovieError( "Internal server error." );
                }
                else
                {
                    setMovieError( error.response.data.error )
                }
                
                setMovie( null );
                
            } );

             if ( response && response.data && response.data.movie )
             {
                setMovie( response.data.movie );
                let genresCopy = JSON.parse( JSON.stringify( response.data.movie.genres ) )
                if ( genresCopy.length > 4 )
                {
                    while ( genresCopy.length > 4 )
                    {
                        genresCopy.pop( );
                    }
                }

                setGenres( genresCopy );
             }
             else
             {
                setMovie( null );
                setGenres([ ]);
             }
        }

        fetchMovieData( );
    }, [ movieId ] )

    return (
        <>
            <title>WatchWok | Dashboard</title>
            
            <BasicHeader sticky={true} />

            <div
                className="min-h-[calc(100vh-128px)] flex flex-col gap-2 md:gap-4 mx-auto max-w-500"
            >
                {
                    movie === null ?
                    (
                        <h2>{movieError}</h2>
                    )
                    :
                    (
                        <div
                            className="relative w-full overflow-hidden max-h-140 rounded-md shadow-md"
                        >
                            <img
                                className="object-center"
                                src={movie.tmdb?.backdrop_url}
                                alt={movie.tmdb?.title + " backdrop"}
                            />
                            <div
                                className="absolute top-0 left-0 right-0 bottom-0 bg-willow-green-200/80 dark:bg-willow-green-800/90 transition-colors"
                            >
                                <div
                                    className="flex flex-col md:flex-row gap-2 md:gap-6 p-5 md:p-10 w-full h-full mx-auto max-w-400"
                                >
                                    <img
                                        className="shadow-md rounded-md shrink-0"
                                        src={movie.tmdb?.poster_url}
                                        alt={movie.tmdb?.title + " poster"}
                                    />
                                    <div
                                        className="flex flex-col gap-2 md:gap-4 grow"
                                    >
                                        <h2
                                            className="font-bold font-2xl md:text-3xl"
                                        >
                                            {movie.tmdb?.title}<span className="font-normal"> | ({movie.year})</span>
                                        </h2>
                                        <div
                                            className="text-md md:font-xl text-slate-700 dark:text-slate-300 flex flex-row gap-2"
                                        >
                                            <span>
                                                {formatDateFull( movie.tmdb.release_date )}
                                            </span>
                                            <span>
                                                -
                                            </span>
                                            <span>
                                                {formatRuntime( movie.tmdb.runtime )}
                                            </span>
                                        </div>
                                        <span
                                            className="font-semibold text-lg"
                                        >
                                            {genres.join( " | " )}
                                        </span>
                                        <div className="flex flex-row gap-1 max-w-fit items-center">
                                            <div className="p-1 rounded-md bg-willow-green-500 dark:bg-willow-green-700 shadow-s">
                                                <StarRating rating={movie.tmdb.vote_average} />
                                            </div>
                                            <span
                                                className="flex items-center justify-center w-12 h-12 shrink-0 bg-willow-green-300 rounded-full text-lg font-bold text-slate-600 shadow-s"
                                            >{Math.round( movie.tmdb.vote_average * 10 ) / 10}</span>
                                        </div>
                                        <div
                                            className="flex flex-row gap-2"
                                        >
                                            <LikeButton movieId={movie.movieId} likedMovies={likedMovies} setLikedMovies={setLikedMovies} />
                                        </div>
                                        <p>
                                            {movie.tmdb?.overview}
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )
                }
            </div>
        </>
    );
}