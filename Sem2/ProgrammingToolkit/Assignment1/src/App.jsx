import { useState } from "react";
import Nav from "./components/Nav";
import HomeSection from "./sections/HomeSection";
import ExperienceSection from "./sections/ExperienceSection";
import HobbiesSection from "./sections/HobbiesSection";

export default function App() {
	const [active, setActive] = useState("home");

	const pages = {
		home: HomeSection,
		experience: ExperienceSection,
		hobbies: HobbiesSection,
	};
	const Page = pages[active];

	return (
		<>
			<div className="noise" />
			<Nav active={active} setActive={setActive} />
			<main className="main">
				<Page key={active} />
			</main>
		</>
	);
}
