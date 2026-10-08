import { useState } from 'react';
import { Link } from 'react-router';
import { apiClient } from '../utils/apiClient';
import { FormError } from './FormError';

export function RegisterForm()
{
    const [ email, setEmail ] = useState( "" );
    const [ username, setUsername ] = useState( "" );
    const [ password, setPassword ] = useState( "" );
    const [ confirmPassword, setConfirmPassword ] = useState( "" );
    const [ error, setError ] = useState( null );

    function handleEmailChange( e )
    {
        setEmail( e.target.value );
    }

    function handleUsernameChange( e )
    {
        setUsername( e.target.value );
    }

    function handlePasswordChange( e )
    {
        setPassword( e.target.value );
    }

    function handleConfirmPasswordChange( e )
    {
        setConfirmPassword( e.target.value );
    }

    function handleFormSubmit( e )
    {
        async function login( formData )
        {
            const response = await apiClient.postForm( "/api/auth/register", formData )
            .catch( ( error ) =>
            {
                if ( error.response.status === 500 )
                {
                    setError( "Internal server error." );
                }
                else
                {
                    setError( error.response.data.error );
                }
            } );

            if ( response && response.data && response.data )
            {
                window.location.href = "/dashboard";
            }
        }

        e.preventDefault( );

        if ( email && username && password && confirmPassword && confirmPassword === password )
        {
            const formData = new FormData( );
            formData.append( "email", email );
            formData.append( "username", username );
            formData.append( "password", password );
            formData.append( "repeat_password", confirmPassword );
            login( formData );
            setError( null );
        }
        else
        {
            const error = `Please ${ !email ? "enter an email" : !username ? "enter a username" : !password ? "enter a password" : !confirmPassword ? "confirm your password" : confirmPassword !== password && "ensure your passwords match" }.`;
            setError( error );
        }
    }
    
    return (
        <form
            className="flex flex-col gap-1 md:gap-2"
            onSubmit={handleFormSubmit}
        >
            <div
                className="flex flex-col gap-1 md:gap-2"
            >
                <label
                    htmlFor="email"
                    className="font-semibold"
                >
                    Email
                </label>
                <input
                    id="email"
                    type="email"
                    placeholder="email@example.com"
                    onChange={handleEmailChange}
                    value={email}
                    className="border-3 focus:border-willow-green-500 box-border transition-[border] outline-0 rounded-md p-1"
                />
            </div>
            <div
                className="flex flex-col gap-1 md:gap-2"
            >
                <label
                    htmlFor="username"
                    className="font-semibold"
                >
                    Username
                </label>
                <input
                    id="username"
                    type="text"
                    placeholder="Username"
                    onChange={handleUsernameChange}
                    value={username}
                    className="border-3 focus:border-willow-green-500 box-border transition-[border] outline-0 rounded-md p-1"
                />
            </div>
            <div
                className="flex flex-col gap-1 md:gap-2"
            >
                <label
                    htmlFor="password"
                    className="font-semibold"
                >
                    Password
                </label>
                <input
                    id="password"
                    type="password"
                    placeholder="Password"
                    onChange={handlePasswordChange}
                    value={password}
                    className="border-3 focus:border-willow-green-500 box-border transition-[border] outline-0 rounded-md p-1"
                />
            </div>
            <div
                className="flex flex-col gap-1 md:gap-2"
            >
                <label
                    htmlFor="confirm_password"
                    className="font-semibold"
                >
                    Confirm password
                </label>
                <input
                    id="confirm_password"
                    type="password"
                    placeholder="Confirm password"
                    onChange={handleConfirmPasswordChange}
                    value={confirmPassword}
                    className="border-3 focus:border-willow-green-500 box-border transition-[border] outline-0 rounded-md p-1"
                />
            </div>
            <button
                type="submit"
                className="active:scale-95 cursor-pointer justify-center bg-willow-green-600 hover:bg-willow-green-700 active:bg-willow-green-800 dark:active:bg-willow-green-200 dark:hover:bg-willow-green-300 dark:bg-willow-green-400 text-white dark:text-black py-2 px-8 text-md font-semibold rounded-md flex items-center shadow-m transition-[background-color,scale] mt-2"
            >
                Register
            </button>
            <Link
                to="/login"
                className="text-center"
            >
                Already have an account?
                <span
                    className="font-bold text-willow-green-500 ml-1 underline"
                >
                    Login instead.
                </span>
            </Link>
            <FormError error={error} />
        </form>
    );
}