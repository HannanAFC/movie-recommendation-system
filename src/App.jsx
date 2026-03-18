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
            if ( sessionStorage.getItem("access_token") )
            {
                const response = await axios.get("/api/auth/@me", {
                    headers: {
                        Authorization: "Bearer " + sessionStorage.getItem( "access_token" )
                    }
                });
                if ( response.data.error )
                {
                    setUser( null );
                }
                else
                {
                    setUser( response.data.user );
                }
            }
            else
            {
                setUser( null );
            }
        }

        fetchUser( );
    }, [ ] );

    return (
        <Routes>
            <Route index element={!user ? <HomePage /> : <Navigate to="/dashboard" replace={true} />} />
            <Route path="/dashboard" element={user ? <DashboardPage user={user} /> : <Navigate to="/login" replace={true} />} />
            <Route path="/login" element={!user ? <LoginPage /> : <Navigate to="/dashboard" replace={true} />} />
            <Route path="/register" element={!user ? <RegisterPage /> : <Navigate to="/dashboard" replace={true} />} />
            <Route path="/reset-password" element={!user ? <ResetPasswordRequestPage /> : <Navigate to="/dashboard" replace={true} />} />
            <Route path="*" element={<NotFoundPage />} />
        </Routes>
    )
}