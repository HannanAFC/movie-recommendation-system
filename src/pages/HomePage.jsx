import { BasicHeader } from '../components/BasicHeader';
import { LoginLink } from '../components/LoginLink';
import { RegisterLink } from '../components/RegisterLink';

export function HomePage( )
{
    return (
        <>
            <title>WatchWok | Get Started</title>
            
            <BasicHeader />

            <div className="flex flex-col mt-4 md:grid grid-cols-2 gap-8 md:gap-2 items-center">
                <div className="flex flex-col gap-4">
                    <h2 className="text-4xl md:text-5xl font-bold">
                        Find your next <span className="text-willow-green-500">big watch</span>
                    </h2>
                    <p className="text-xl">
                        WatchWok is designed to provide you with the most accurate movie recommendations, no matter your preferences.
                    </p>
                    <p className="text-xl">
                        Our algorithm uses filtering methods that are designed around your personal ratings of films; the more you rate, the more accurate the predictions!
                    </p>

                    <div className="flex flex-row gap-4">
                        <LoginLink />
                        <RegisterLink />
                    </div>
                </div>
                <picture>
                    <source media="(width < 769px)" srcset="https://placehold.co/400x400" />
                    <source media="(width >= 769px)" srcset="https://placehold.co/500x500 1x, https://placehold.co/1000x1000 2x" />
                    <img src="https://placehold.co/1000x1000" alt="WatchWork Dashboard" />
                </picture>
            </div>
        </>
    );
}