FROM golang:1.22 AS build
WORKDIR /src
COPY go.mod ./
COPY *.go ./
RUN CGO_ENABLED=0 go build -o /probe .

FROM gcr.io/distroless/static:nonroot
COPY --from=build /probe /probe
USER nonroot
ENTRYPOINT ["/probe"]
