import axios from "axios";

const API = axios.create({
  baseURL: "http://127.0.0.1:8000",
});

export const generateData = () => API.post("/generate-data");
export const trainModel = () => API.post("/train-model");
export const getMachines = () => API.get("/machines");
export const getHighRisk = () => API.get("/high-risk-machines");

export const simulateMaintenance = () => API.get("/simulate-maintenance");

export const getJobs = () => API.get("/jobs");

export const optimizeSchedule = (weights?: {
  w_throughput?: number;
  w_risk?: number;
  w_cost?: number;
}) =>
  API.post("/optimize-schedule", null, {
    params: weights,
  });

export default API;
// ⭐ Schedule optimization
