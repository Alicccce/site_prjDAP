import { positions } from '../mocks/position.js'
import { getAnalysisResult } from '../mocks/skills.js'
import { getAnalysisResult as getAnalysisResultAlt } from '../mocks/analysis_result.js'
import { userProfile } from '../mocks/user_profile.js'

const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms))

export const mockApi = {
  async getPositions() {
    await delay(500)
    return positions
  },

  async analyzeByPosition(jobTitle) {
    await delay(800)
    return getAnalysisResult(jobTitle)
  },

  async getUserProfile() {
    await delay(300)
    return userProfile
  },

  async saveUserSkills(skills) {
    await delay(600)
    console.log('Сохранённые навыки:', skills)
    return { success: true }
  }
}