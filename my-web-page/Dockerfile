FROM nginx:alpine

# Remove default nginx website
RUN rm -rf /usr/share/nginx/html/*

# Copy files as root (this ensures proper permissions)
COPY index.html /usr/share/nginx/html/
COPY Fliq.js /usr/share/nginx/html/

# Set proper permissions explicitly
RUN chmod 755 /usr/share/nginx/html
RUN chmod 644 /usr/share/nginx/html/*

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]