import { useEffect, useState } from 'react';
import { Navigate, Route, Routes } from 'react-router';
import axios from 'axios';
import { getCookie } from './utils/getCookie';
import { HomePage } from './pages/HomePage';
import { DashboardPage } from './pages/DashboardPage';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { ResetPasswordRequestPage } from './pages/ResetPasswordRequestPage';
import { SelectDatasetPage } from './pages/SelectDatasetPage';
import { LikeMoviesPage } from './pages/LikeMoviesPage';
import { NotFoundPage } from './pages/NotFoundPage';

export default function App( )
{
    const [ user, setUser ]                               = useState( null );
    const [ isLoading, setIsLoading ]                     = useState( true );
    const [ datasetSelected, setDatasetSelected ]         = useState( false );
    const [ needsToSelectMovies, setNeedsToSelectMovies ] = useState( true );

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
            }

            setIsLoading( false );
        }

        fetchUser( );
    }, [ ] );

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
                path="/select-a-dataset"
                element=
                {
                    user ?
                    (
                        !datasetSelected ? <SelectDatasetPage setDatasetSelected={setDatasetSelected} /> : <Navigate to="/dashboard" replace={true} />
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
                        datasetSelected ?
                        (
                            needsToSelectMovies ? <LikeMoviesPage /> : <Navigate to="/dashboard" replace={true} />
                        ) : <Navigate to="/select-a-dataset" replace={true} />
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
                            !needsToSelectMovies ? <DashboardPage user={user} /> : <Navigate to="/select-your-favourites" replace={true} />
                        ) : <Navigate to="/select-a-dataset" replace={true} />
                    ) : <Navigate to="/login" replace={true} />
                }
            />
            <Route path="*" element={<NotFoundPage />} />
        </Routes>
    );
}