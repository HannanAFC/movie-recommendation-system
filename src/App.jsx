import { useEffect, useState } from 'react';
import { Navigate, Route, Routes } from 'react-router';
import axios from 'axios';
import { getCookie } from './utils/getCookie';
import { HomePage } from './pages/HomePage';
import { DashboardPage } from './pages/DashboardPage';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { ResetPasswordRequestPage } from './pages/ResetPasswordRequestPage';
import { OnboardingPage } from './pages/OnboardingPage';
import { LikeMoviesPage } from './pages/LikeMoviesPage';
import { MoviePage } from './pages/MoviePage';
import { NotFoundPage } from './pages/NotFoundPage';
import './types/user';

export default function App( )
{
    /** @type {[User, React.Dispatch<React.SetStateAction<User>>]} */
    const [ user, setUser ]                               = useState( null );
    const [ isLoading, setIsLoading ]                     = useState( true );
    const [ datasetSelected, setDatasetSelected ]         = useState( false );
    const [ onboardingComplete, setOnboardingComplete ]   = useState( false );
    const [ needsToSelectMovies, setNeedsToSelectMovies ] = useState( true );
    const [ tmdbApiKeyStatus, setTmdbApiKeyStatus ]       = useState( null );
    const [ likedMovies, setLikedMovies ]                 = useState( new Set( ) )

    useEffect( ( ) =>
    {
        async function fetchUser( )
        {
            const response = await axios.get(
                "/api/auth/@me",
                {
                    headers:
                    {
                        "X-CSRF-TOKEN": getCookie( "csrf_access_token" )
                    }
                }
            )
            .catch( ( error ) =>
            {
                if ( error.response.status === 401 )
                {
                    setUser( null );
                }
            } );

            if ( response && response.data && response.data.user )
            {
                setUser( response.data.user );
                setDatasetSelected( response.data.user.dataset_selected );
                setNeedsToSelectMovies( response.data.user.needs_to_select_movies );
                setTmdbApiKeyStatus( response.data.user.tmdb );
                const apiKeySet         = response.data.user.tmdb.api_key_set;
                const apiKeyValid       = response.data.user.tmdb.api_key_valid;
                const datasetIsSelected = response.data.user.dataset_selected;
                setOnboardingComplete( apiKeySet && apiKeyValid && datasetIsSelected );
            }

            setIsLoading( false );
        }

        fetchUser( );
    }, [ ] );

    useEffect( () =>
    {
        async function fetchLikedMovies( )
        {
            const response = await axios.get( "/api/movies/liked" )
            .catch( ( error ) =>
            {
                if ( error.response.status === 401 )
                {
                    setLikedMovies( new Set( ) );
                }
            } );

            if ( response && response.data )
            {
                setLikedMovies( new Set(response.data.liked_movie_ids ) );
            }
        }

        if ( user )
        {
            fetchLikedMovies( );
        }
    }, [ user ] )

    // Defer rendering until the user API request is complete
    if ( isLoading )
    {
        return null;
    }

    // Routes are a little complicated as there are checks for if the user is logged in,
    // needs to select a dataset and if they need to like movies. The routes are explained
    // using diagrams to make understanding them easier.
    return (
        <Routes>
            {/*
            Index page route:
                !user -> index
                      -> dashboard
            */}
            <Route
                index
                element=
                {
                    !user ? <HomePage /> : <Navigate to="/dashboard" replace={true}/>
                }
            />
            {/*
            Login page route:
                !user -> login
                      -> dashboard
            */}
            <Route
                path="/login"
                element=
                {
                    !user ? <LoginPage /> : <Navigate to="/dashboard" replace={true} />
                }
            />
            {/*
            Login page route:
                !user -> register
                      -> dashboard
            */}
            <Route
                path="/register" 
                element=
                {
                    !user ? <RegisterPage /> : <Navigate to="/dashboard" replace={true} />
                }
            />
            {/*
            Reset password page route:
                !user -> reset password
                      -> dashboard
            */}
            <Route
                path="/reset-password"
                element=
                {
                    !user ? <ResetPasswordRequestPage /> : <Navigate to="/dashboard" replace={true} />
                }
            />
            {/*
            Select a dataset page route:
                user -> !datasetSelected -> select a dataset
                                         -> dashboard
                     -> login
            */}
            <Route
                path="/onboarding"
                element=
                {
                    user ?
                    (
                        !onboardingComplete ? <OnboardingPage
                            setOnboardingComplete={setOnboardingComplete}
                            datasetSelected={datasetSelected}
                            setDatasetSelected={setDatasetSelected}
                            tmdbApiKeyStatus={tmdbApiKeyStatus}
                            setTmdbApiKeyStatus={setTmdbApiKeyStatus}
                            setUser={setUser}
                        /> : <Navigate to="/dashboard" replace={true} />
                    ) : <Navigate to="/login" replace={true} />
                }
            />
            {/*
            Select liked movies page
                user -> !datasetSelected -> needsToSelectMovies -> select liked movies
                                                                -> dashboard
                                         -> select a dataset
                     -> login
            */}
            <Route
                path="/select-your-favourites"
                element=
                {
                    user ?
                    (
                        onboardingComplete ?
                        (
                            needsToSelectMovies ? <LikeMoviesPage
                                setNeedsToSelectMovies={setNeedsToSelectMovies}
                                likedMovies={likedMovies}
                                setLikedMovies={setLikedMovies}
                                setUser={setUser}
                            /> : <Navigate to="/dashboard" replace={true} />
                        ) : <Navigate to="/onboarding" replace={true} />
                    ) : <Navigate to="/login" replace={true} />
                }
            />
            {/*
            Dashboard page
                user -> datasetSelected -> !needsToSelectMovies -> dashboard
                                                                -> select liked movies
                                         -> select a dataset
                     -> login
            */}
            <Route
                path="/dashboard"
                element=
                {
                    user ?
                    (
                        datasetSelected ?
                        (
                            !needsToSelectMovies ?
                            <DashboardPage
                                user={user}
                                likedMovies={likedMovies}
                                setLikedMovies={setLikedMovies}
                                setUser={setUser}
                            /> : <Navigate to="/select-your-favourites" replace={true} />
                        ) : <Navigate to="/onboarding" replace={true} />
                    ) : <Navigate to="/login" replace={true} />
                }
            />
            <Route
                path="/movies/:movieId"
                element=
                {
                    user ?
                    (
                        datasetSelected ?
                        (
                            !needsToSelectMovies ?
                            <MoviePage
                                user={user}
                                likedMovies={likedMovies}
                                setLikedMovies={setLikedMovies}
                                setUser={setUser}
                            /> : <Navigate to="/select-your-favourites" replace={true} />
                        ) : <Navigate to="/onboarding" replace={true} />
                    ) : <Navigate to="/login" replace={true} />
                }
            />
            <Route path="*" element={<NotFoundPage />} />
        </Routes>
    );
}