
import NavigateBar from './NavigateBar'

function Header() {
    return (
        <header className="Header" style={
            {
                height: '4em',
                backgroundColor: '#646464',
            }
        }>
            <NavigateBar/>
        </header>
    )
}

export default Header;

