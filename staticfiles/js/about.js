
  const techSkills = [
    'Python', 'C++', 'Java', 'Django', 'React.js', 
    'Kali Linux', 'Ethical Hacking', 'Cybersecurity', 
    'Network Security', 'Penetration Testing'
  ];

  const passions = [
    'coding', 'ethical hacking', 'gaming (PUBG, Free Fire, GTA 5, Minecraft)', 
    'GATE exam prep', 'romantic shayari', 'life advice'
  ];

  const values = [
    'relentless curiosity', 'unwavering dedication', 'a hunger for knowledge', 
    'passion for perfection', 'heart full of empathy', 'mind sharp like a blade', 
    'spirit that never settles'
  ];

  const lifeQuotes = [
    '“Life is a code — sometimes buggy, always beautiful.”',
    '“In every failure lies the seed of a stronger comeback.”',
    '“Dream big, hustle hard, and code your destiny.”',
    '“When passion leads, success follows.”',
    '“The greatest hack is to live authentically.”',
    '“From the darkest nights emerge the brightest stars.”',
  ];

  function getRandom(arr) {
    return arr[Math.floor(Math.random() * arr.length)];
  }

  function generateAboutText() {
    return `
      By day, I wield my skills in <strong>${getRandom(techSkills)}</strong> and <strong>${getRandom(techSkills)}</strong>, crafting solutions 
      that bridge logic and creativity.<br><br>
      
      Driven by <strong>${getRandom(values)}</strong>, I dive deep into <strong>${getRandom(passions)}</strong>, 
      whether it’s the thrill of ethical hacking or the poetry hidden in romantic shayari.<br><br>
      
      Every challenge I face, every bug I squash, is a step toward mastery — not just of code, but of life itself.<br><br>
      
      I am Villen Bhai — a seeker, a creator, a dreamer, and above all, a believer that the journey 
      matters more than the destination.<br><br>
      
      <em>${getRandom(lifeQuotes)}</em>
    `;
  }

  const aboutElem = document.getElementById('dynamic-about');

  function updateAbout() {
    aboutElem.style.opacity = 0;
    setTimeout(() => {
      aboutElem.innerHTML = generateAboutText();
      aboutElem.style.opacity = 1;
    }, 600);
  }

  document.addEventListener('DOMContentLoaded', () => {
    updateAbout();
    setInterval(updateAbout, 20000);
  });

