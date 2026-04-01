import { useState } from 'react';
import axios from 'axios';

export function LikeButton({ movieId, setCanContinue, likedMovies, setLikedMovies })
{
    const [ disabled, setDisabled ] = useState( false );
    const isLiked                   = likedMovies.has( movieId );

    async function removeFromLikes( )
    {
        const response = await axios.delete( `/api/movies/like/${movieId}` )
        .catch( ( error ) =>
        {
            console.log( error.response.data.error );
        } );

        if ( response && response.data )
        {
            setCanContinue( !response.data.needs_to_select_movies );
            setLikedMovies( ( prevLikedMovies ) =>
            {
                const nextLikedMovies = new Set( prevLikedMovies );
                nextLikedMovies.delete( movieId );
                return nextLikedMovies;
            } );
        }

        setDisabled( false );
    }

    async function addToLikes( )
    {
        const response = await axios.post( `/api/movies/like/${movieId}` )
        .catch( ( error ) =>
        {
            console.log( error.response.data.error );
        } );

        if ( response && response.data )
        {
            setCanContinue( !response.data.needs_to_select_movies );
            setLikedMovies( ( prevLikedMovies ) =>
            {
                const nextLikedMovies = new Set( prevLikedMovies );
                nextLikedMovies.add( movieId );
                return nextLikedMovies;
            } );
        }

        setDisabled( false );
    }

    function handleLikeClick( )
    {
        setDisabled( true );

        if ( isLiked )
        {
            removeFromLikes( );
        }
        else
        {
            addToLikes( );
        }
    }

    if ( isLiked )
    {
        return (
            <button
                aria-label="Remove movie from likes"
                onClick={handleLikeClick}
                disabled={disabled}
                className="flex items-center justify-center w-10 h-10 bg-willow-green-300 p-1 pt-1.5 fill-willow-green-700 rounded-full shrink-0 shadow-m hover:bg-willow-green-400 hover:fill-willow-green-800 transition-[background-color,fill,scale] cursor-pointer active:scale-95"
            >
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 640"><path d="M305 151.1L320 171.8L335 151.1C360 116.5 400.2 96 442.9 96C516.4 96 576 155.6 576 229.1L576 231.7C576 343.9 436.1 474.2 363.1 529.9C350.7 539.3 335.5 544 320 544C304.5 544 289.2 539.4 276.9 529.9C203.9 474.2 64 343.9 64 231.7L64 229.1C64 155.6 123.6 96 197.1 96C239.8 96 280 116.5 305 151.1z"/></svg>
            </button>
        );
    }
    else
    {
        return (
            <button
                aria-label="Add movie to likes"
                onClick={handleLikeClick}
                disabled={disabled}
                className="flex items-center justify-center w-10 h-10 bg-willow-green-300 p-1 pt-1.5 fill-willow-green-700 rounded-full shrink-0 shadow-m hover:bg-willow-green-400 hover:fill-willow-green-800 transition-[background-color,fill,scale] cursor-pointer active:scale-95"
            >
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 640"><path d="M442.9 144C415.6 144 389.9 157.1 373.9 179.2L339.5 226.8C335 233 327.8 236.7 320.1 236.7C312.4 236.7 305.2 233 300.7 226.8L266.3 179.2C250.3 157.1 224.6 144 197.3 144C150.3 144 112.2 182.1 112.2 229.1C112.2 279 144.2 327.5 180.3 371.4C221.4 421.4 271.7 465.4 306.2 491.7C309.4 494.1 314.1 495.9 320.2 495.9C326.3 495.9 331 494.1 334.2 491.7C368.7 465.4 419 421.3 460.1 371.4C496.3 327.5 528.2 279 528.2 229.1C528.2 182.1 490.1 144 443.1 144zM335 151.1C360 116.5 400.2 96 442.9 96C516.4 96 576 155.6 576 229.1C576 297.7 533.1 358 496.9 401.9C452.8 455.5 399.6 502 363.1 529.8C350.8 539.2 335.6 543.9 320 543.9C304.4 543.9 289.2 539.2 276.9 529.8C240.4 502 187.2 455.5 143.1 402C106.9 358.1 64 297.7 64 229.1C64 155.6 123.6 96 197.1 96C239.8 96 280 116.5 305 151.1L320 171.8L335 151.1z"/></svg>
            </button>
        );
    }
}