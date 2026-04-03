export const getAnalysisResult = (jobTitle) => {
  const mockData = {
    "Data Scientist": {
      jobTitle: "Data Scientist",
      skills: [
        { name: "Python", frequency: 95, importance: "mandatory" },
        { name: "SQL", frequency: 87, importance: "mandatory" },
        { name: "Machine Learning", frequency: 82, importance: "mandatory" },
        { name: "Tableau", frequency: 35, importance: "optional" },
        { name: "Apache Spark", frequency: 30, importance: "optional" }
      ],
      totalVacancies: 150
    },
    "Frontend Developer": {
      jobTitle: "Frontend Developer",
      skills: [
        { name: "JavaScript", frequency: 98, importance: "mandatory" },
        { name: "Vue.js", frequency: 65, importance: "mandatory" },
        { name: "CSS", frequency: 92, importance: "mandatory" },
        { name: "React", frequency: 70, importance: "optional" },
        { name: "TypeScript", frequency: 55, importance: "optional" }
      ],
      totalVacancies: 320
    }
  }
  return mockData[jobTitle] || mockData["Frontend Developer"]
}