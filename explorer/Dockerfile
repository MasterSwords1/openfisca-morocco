FROM node:14-bullseye AS build
WORKDIR /app
ARG API_URL=http://localhost:5000
COPY explorer/patches/legislation-explorer.patch /tmp/legislation-explorer.patch
RUN git clone https://github.com/openfisca/legislation-explorer.git . \
    && git checkout 8a93870bd055e3bec2a7dbbe826730b43ec96a4a \
    && git apply /tmp/legislation-explorer.patch \
    && rm -rf .git
ENV API_URL=${API_URL}
RUN npm install --production && npm run build

FROM node:14-bullseye-slim AS runtime
WORKDIR /app
ENV NODE_ENV=production HOST=0.0.0.0 PORT=2020
COPY --from=build /app/package.json /app/package-lock.json ./
COPY --from=build /app/.babelrc ./
COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/src ./src
COPY --from=build /app/index.js ./index.js
COPY --from=build /app/public ./public
COPY --from=build /app/webpack-assets.json ./webpack-assets.json
COPY --from=build /app/webpack.config.prod.babel.js ./webpack.config.prod.babel.js
CMD ["npm", "start"]
