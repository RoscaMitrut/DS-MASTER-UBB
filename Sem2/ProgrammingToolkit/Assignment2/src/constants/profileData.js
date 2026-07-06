const profileData = {
  personal: {
    name: "Roșca Eduard-Mitruț",
    title: "Software Developer",
    dateOfBirth: "April 17, 2003",
    location: "Cluj-Napoca, Romania",
    email: "reduardmitrut@gmail.com",
    placesLived: ["Cluj-Napoca, Romania", "Sărmaș, Romania", "Dârjiu, Romania", "asdf"],
    languages: ["Romanian (Native)", "English (Fluent)", "Hungarian (Elementary)"],
    social: {
      github: "https://github.com/RoscaMitrut",
      linkedin: "https://www.linkedin.com/in/eduard-mitrut-rosca-329238225/",
    },
  },

  professional: {
    experience: [
      {
        role: "Master's in Data Science",
        company: "Babeș-Bolyai University",
        period: "Oct 2025 - Present",
      },
      {
        role: "Bachelor's in Computer Science",
        company: "Babeș-Bolyai University",
        period: "Oct 2022 - Jul 2025",
      },
    ],
    skills: [
      { category: "Programming Languages", items: ["Python", "C/C++", "C#", "Java", "JavaScripts"] },
      { category: "Frameworks", items: ["Spring", "React", "ASP.NET Core"] },
      { category: "Machine Learning", items: ["TensorFlow", "Keras", "NumPy", "Pandas", "Matplotlib"] },
      { category: "Version Control", items: ["Git", "GitHub"] },
      { category: "Others", items: ["SQL", "Linux", "Docker"] }
      ,
    ],
    certifications: [
      { name: "CAE C1 Advanced English Certificate", issuer: "Cambridge University Press & Assessment", year: "2021" },
      { name: "Digital Literacy Certificate - ECDL", issuer: "ICDL Foundation", year: "2021" },
    ],
  },

  hobbies: {
    passions: [
      {
        icon: "🎵",
        title: "Music",
        description:
          "Listening to music, mostly Rap, but lately also Indie Rock and Heavy Metal.",
      },
      {
        icon: "🏔️",
        title: "Hiking",
        description:
          "Exploring the sceneries the Carpathians have to offer, mostly hiking by myself to also clear my mind.",
      },
      {
        icon: "🎮",
        title: "Gaming",
        description:
          "Mostly MMORPG's when I'm alone and all types of LAN games when I'm with friends.",
      },
      {
        icon: "🛠️",
        title: "Tinkering",
        description:
          "Fixing and modifying stuff for my relatives and around the house.",
      },
    ],
  },
};

export default profileData;