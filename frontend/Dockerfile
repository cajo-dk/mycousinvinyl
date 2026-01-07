# Build stage
FROM node:20-alpine as build

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build arguments for environment variables
ARG VITE_API_URL
ARG VITE_AZURE_CLIENT_ID
ARG VITE_AZURE_TENANT_ID
ARG VITE_AZURE_REDIRECT_URI
ARG VITE_AZURE_GROUP_ADMIN
ARG VITE_MANIFEST_ENV
ARG VITE_NPM_BUILD_SCRIPT=build

# Export as environment variables for Vite
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_AZURE_CLIENT_ID=$VITE_AZURE_CLIENT_ID
ENV VITE_AZURE_TENANT_ID=$VITE_AZURE_TENANT_ID
ENV VITE_AZURE_REDIRECT_URI=$VITE_AZURE_REDIRECT_URI
ENV VITE_AZURE_GROUP_ADMIN=$VITE_AZURE_GROUP_ADMIN
ENV VITE_MANIFEST_ENV=$VITE_MANIFEST_ENV

# Debug: Print environment variables
RUN echo "VITE_AZURE_CLIENT_ID=$VITE_AZURE_CLIENT_ID" && \
    echo "VITE_AZURE_TENANT_ID=$VITE_AZURE_TENANT_ID" && \
    echo "VITE_AZURE_REDIRECT_URI=$VITE_AZURE_REDIRECT_URI" && \
    echo "VITE_AZURE_GROUP_ADMIN=$VITE_AZURE_GROUP_ADMIN" && \
    echo "VITE_MANIFEST_ENV=$VITE_MANIFEST_ENV"

# Build the application
RUN npm run $VITE_NPM_BUILD_SCRIPT

# Production stage
FROM nginx:alpine

# Copy built assets from build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose HTTPS port
EXPOSE 443

CMD ["nginx", "-g", "daemon off;"]
