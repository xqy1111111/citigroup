export const config = {
  baseUrl: 'http://localhost:8000',

  processUrl: (fileId: string) => `/process/${fileId}/process`,
};