function Nav({ active, setActive }) {
	const links = [
		{ id: "home", label: "About" },
		{ id: "experience", label: "Experience" },
		{ id: "hobbies", label: "Hobbies" },
	];
	return (
		<nav className="nav">
			<span className="nav-logo">
				MyProfile
			</span>
			<ul className="nav-links">
				{links.map((l) => (
					<li key={l.id}>
						<button
							className={`nav-btn ${active === l.id ? "nav-btn--active" : ""}`}
							onClick={() => setActive(l.id)}
						>
							{l.label}
						</button>
					</li>
				))}
			</ul>
		</nav>
	);
}

export default Nav;