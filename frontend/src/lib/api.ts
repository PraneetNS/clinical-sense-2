import axios from 'axios';

const api = axios.create({
    baseURL: process.env.VITE_API_URL,
});

api.interceptors.request.use((config: any) => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response && error.response.status === 401) {
            if (typeof window !== 'undefined') {
                localStorage.removeItem('token');
                window.location.href = '/login';
            }
        }
        return Promise.reject(error);
    }
);

export const notesApi = {
    getAll: (search?: string, mode: string = 'keyword') => api.get('/notes/', { params: { search, mode } }),
    getById: (id: string) => api.get(`/notes/${id}`),
    create: (data: { raw_content: string; title: string; note_type?: string; patient_id?: number }) => api.post('/notes/structure', data),
    generateSoap: (id: string | number) => api.post(`/notes/${id}/generate`),
    update: (id: string | number, data: any) => api.put(`/notes/${id}`, data),
    delete: (id: string | number) => api.delete(`/notes/${id}`),
    getAudit: (id: string | number) => api.get(`/notes/${id}/audit`),
    getHistory: (id: string | number) => api.get(`/notes/${id}/history`),
};

export const patientsApi = {
    getAll: (search?: string) => api.get('/patients/', { params: { search } }),
    getById: (id: string | number) => api.get(`/patients/${id}`),
    getTimeline: (id: string | number) => api.get(`/patients/${id}/timeline`),
    create: (data: { name: string; mrn: string; date_of_birth?: string }) => api.post('/patients/', data),
    update: (id: string | number, data: any) => api.patch(`/patients/${id}`, data),
    getReport: (id: string | number) => api.get(`/patients/${id}/report`),
    downloadReportPdf: (id: string | number) => api.get(`/patients/${id}/report/pdf`, { responseType: 'blob' }),
    toggleStatus: (id: string | number, status: string) => api.patch(`/patients/${id}`, { status }),
};

export const clinicalApi = {
    // Medical History
    getHistory: (patientId: string | number) => api.get(`/patients/${patientId}/history`),
    addHistory: (patientId: string | number, data: any) => api.post(`/patients/${patientId}/history`, data),
    updateHistory: (id: string | number, data: any) => api.put(`/patients/history/${id}`, data),
    deleteHistory: (id: string | number) => api.delete(`/patients/history/${id}`),

    // Medications
    getMedications: (patientId: string | number) => api.get(`/patients/${patientId}/medications`),
    addMedication: (patientId: string | number, data: any) => api.post(`/patients/${patientId}/medications`, data),
    updateMedication: (id: string | number, data: any) => api.put(`/patients/medications/${id}`, data),
    deleteMedication: (id: string | number) => api.delete(`/patients/medications/${id}`),

    // Allergies
    addAllergy: (patientId: string | number, data: any) => api.post(`/patients/${patientId}/allergies`, data),
    updateAllergy: (id: string | number, data: any) => api.put(`/patients/allergies/${id}`, data),
    deleteAllergy: (id: string | number) => api.delete(`/patients/allergies/${id}`),

    // Admissions
    getAdmissions: (patientId: string | number) => api.get(`/patients/${patientId}/admissions`),
    addAdmission: (patientId: string | number, data: any) => api.post(`/patients/${patientId}/admissions`, data),
    updateAdmission: (id: string | number, data: any) => api.put(`/patients/admissions/${id}`, data),
    deleteAdmission: (id: string | number) => api.delete(`/patients/admissions/${id}`),

    // Procedures
    getProcedures: (patientId: string | number) => api.get(`/patients/${patientId}/procedures`),
    addProcedure: (patientId: string | number, data: any) => api.post(`/patients/${patientId}/procedures`, data),
    updateProcedure: (id: string | number, data: any) => api.put(`/patients/procedures/${id}`, data),
    deleteProcedure: (id: string | number) => api.delete(`/patients/procedures/${id}`),

    // Documents
    getDocuments: (patientId: string | number) => api.get(`/patients/${patientId}/documents`),
    uploadDocument: (patientId: string | number, formData: FormData) => api.post(`/patients/${patientId}/documents/upload`, formData, { headers: { 'Content-Type': 'multipart/form-data' } }),
    addDocument: (patientId: string | number, data: any) => api.post(`/patients/${patientId}/documents`, data),
    updateDocument: (id: string | number, data: any) => api.put(`/patients/documents/${id}`, data),
    deleteDocument: (id: string | number) => api.delete(`/patients/documents/${id}`),

    // Tasks
    getTasks: (patientId: string | number) => api.get(`/patients/${patientId}/tasks`),
    addTask: (patientId: string | number, data: any) => api.post(`/patients/${patientId}/tasks`, data),
    updateTask: (id: string | number, data: any) => api.put(`/patients/tasks/${id}`, data),
    deleteTask: (id: string | number) => api.delete(`/patients/tasks/${id}`),

    // Billing
    getBilling: (patientId: string | number) => api.get(`/patients/${patientId}/billing`),
    addBilling: (patientId: string | number, data: any) => api.post(`/patients/${patientId}/billing`, data),
    updateBilling: (id: string | number, data: any) => api.put(`/patients/billing/${id}`, data),
    deleteBilling: (id: string | number) => api.delete(`/patients/billing/${id}`),
};

export const authApi = {
    login: (data: FormData) => api.post('/auth/login', data),
    register: (data: any) => api.post('/auth/register', data),
    getMe: () => api.get('/auth/me'),
};

export default api;
