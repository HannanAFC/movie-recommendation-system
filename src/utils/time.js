export function formatRuntime( time )
{
    if ( !parseInt( time ) && time <= 0  )
    {
        return "0m";
    }
    
    const hours = Math.floor( time / 60 )
    const minutes = time - hours * 60;

    let runtimeString = "";

    if ( hours > 0 )
    {
        runtimeString = hours + "h ";
    }

    runtimeString += minutes + "m"

    return runtimeString;
}