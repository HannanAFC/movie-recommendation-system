import axios from 'axios';
import { BasicHeader } from '../components/BasicHeader'
import { RecommendationsSlider } from '../components/RecommendationsSlider';
import { useNotification } from '../hooks/useNotification';
import { NotificationPopup } from '../components/NotificationPopup';
import '../types/user';
import { useEffect, useState } from 'react';
import { InitialiseRecommenderButton } from '../components/InitialiseRecommenderButton';
import { CreateRecommendationButton } from '../components/CreateRecommendationButton';
import { Footer } from '../components/Footer';

/**
 * @param {{ user: User }} props
 */
export function DashboardPage({ user, likedMovies, setLikedMovies, setUser })
{
    const [ recommendations, setRecommendations ]         = useState([ ]);
    const [ recommendationError, setRecommendationError ] = useState( null );

    const {
        notification,
        showNotification,
        hideNotification
    } = useNotification( );

    useEffect( ( ) =>
    {
        if ( user.recommender.needs_manual_initialisation )
        {
            showNotification(
            {
                type: "warning",
                content: (
                    <div
                        className="flex flex-col gap-1"
                    >
                        <span>
                            {user.recommender.status_message}
                        </span>
                        <InitialiseRecommenderButton user={user} showNotification={showNotification} />
                    </div>
                )
            })
        }
    }, [ ] )

    useEffect( ( ) =>
    {
        async function fetchLatestRecommendation( )
        {
            if ( !user.recommender.is_ready )
            {
                setRecommendationError( user.recommender.status_message );
                return;
            }

            const response = await axios.get( "/api/recommendations/latest" )
            .catch( ( error ) =>
            {
                if ( error.response.status === 500 )
                {
                    setRecommendationError( "Internal server error." );
                }
                else
                {
                    setRecommendationError( error.response.data.error )
                }
                
                setRecommendations([ ]);
                
            } );

            if ( response && response.data && response.data.recommendation_set && response.data.recommendation_set.movies )
            {
                if ( response.data.recommendation_set.movies.length && response.data.recommendation_set.movies.length > 0  )
                {
                    setRecommendations( response.data.recommendation_set.movies );
                }
                else
                {
                    setRecommendationError( 
                        <div className="flex flex-col gap-2">
                            You don't have any recommendations.
                            <CreateRecommendationButton setRecommendations={setRecommendations} />
                        </div>
                     )
                }
            }
            else
            {
                setRecommendationError( "You have no recommendations yet, click below to create some!" );
            }
        }

        fetchLatestRecommendation( );

        return ( ) =>
        {
            setRecommendationError( "" );
            setRecommendations([ ]);
        }
    }, [ user.recommender ] );

    return (
        <>
            <title>WatchWok | Dashboard</title>
            
            <BasicHeader sticky={true} />

            <div
                className="min-h-[calc(100vh-128px)] flex flex-col gap-2 md:gap-4 mx-auto"
            >
                <section
                    className="flex flex-col gap-4"
                >
                    <RecommendationsSlider
                        likedMovies={likedMovies}
                        setLikedMovies={setLikedMovies} 
                        recommendations={recommendations}
                        recommendationError={recommendationError}
                    />
                    <div
                        className="flex flex-row gap-4 items-center"
                    >
                        <h4
                            className="font-semibold text-xl"
                        >
                            Not happy with these recommendations?
                        </h4>
                        <CreateRecommendationButton setRecommendations={setRecommendations}  />
                    </div>
                </section>
            </div>

            <NotificationPopup
                isOpen={notification.isOpen}
                type={notification.type}
                content={notification.content}
                dismissable={notification.dismissable}
                timeout={notification.timeout}
                onClose={hideNotification}
            />
            <Footer setUser={setUser} />
        </>
    );
}