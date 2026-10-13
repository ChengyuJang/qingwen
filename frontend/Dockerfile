# ---------- 阶段 1：构建 ----------
FROM node:20-alpine AS builder

WORKDIR /app

# 先装依赖（缓存层）
COPY package.json package-lock.json ./
RUN npm ci

# 复制代码并构建
COPY . .
RUN npm run build

# ---------- 阶段 2：Nginx 托管 ----------
FROM nginx:alpine

# 拷贝构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

# 拷贝自定义 Nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]