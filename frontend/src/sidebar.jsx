// ... existing code ...
function SideBar(){
    const [expandedRepos, setExpandedRepos] = useState({});

    const toggleRepo = (repoName) => {
        setExpandedRepos(prev => ({
            ...prev,
            [repoName]: !prev[repoName]
        }));
    };

    return (
        <div className="sidebar">
            <h1>Repositories</h1>
            {repos.map((repo) => (
                <div key={repo.name} className="repo-item">
                    <div
                        className="repo-header"
                        onClick={() => toggleRepo(repo.name)}
                    >
                        <span>{expandedRepos[repo.name] ? '▼' : '▶'}</span>
                        <span>{repo.name}</span>
                    </div>
                    {expandedRepos[repo.name] && (
                        <div className="repo-files">
                            {repo.files.map((file) => (
                                <div key={file.path} className="file-item">
                                    {file.name}
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            ))}
        </div>
    )
}

// ... existing code ...

