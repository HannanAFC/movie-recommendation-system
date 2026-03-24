import { useEffect, useState } from 'react';
import { Navigate, Route, Routes } from  'react-router';
import axios from 'axios';
import { HomePage } from './pages/HomePage';
import { DashboardPage } from './pages/DashboardPage';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { ResetPasswordRequestPage } from './pages/ResetPasswordRequestPage';
import { NotFoundPage } from './pages/NotFoundPage';

export default function App( )
{
    const [ user, setUser ] = useState(null);
    useEffect( ( ) =>
    {
        async function fetchUser( )
        {
            const response = await axios.get(
                "/api/auth/@me",
            ).catch( ( error ) =>
            {
                if ( error.response.status === 401 )
                {
                    setUser( null );
                }
            } );

            if ( response && response.data && response.data.user )
            {
                setUser( response.data.user );
            }
        }

        fetchUser( );
    }, [ ] );

    return (
        <Routes>
            <Route index element={!user ? <HomePage /> : <Navigate to="/dashboard" replace={true} />} />
            <Route path="/dashboard" element={user ? <DashboardPage user={user} setUser={setUser} /> : <Navigate to="/login" replace={true} />} />
            <Route path="/login" element={!user ? <LoginPage /> : <Navigate to="/dashboard" replace={true} />} />
            <Route path="/register" element={!user ? <RegisterPage /> : <Navigate to="/dashboard" replace={true} />} />
            <Route path="/reset-password" element={!user ? <ResetPasswordRequestPage /> : <Navigate to="/dashboard" replace={true} />} />
            <Route path="*" element={<NotFoundPage />} />
        </Routes>
    )
}