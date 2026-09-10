# Stremio + Web Admin separado — instalação inicial

Esta distribuição usa o fork `emmanique/stremio-libtorrent-server-webadmin` como base e executa o Web Admin num contentor independente. A reconstrução ou actualização do Stremio não substitui o HTML, a API, o estado ou os logs administrativos.

## Volumes

| Volume | Serviço principal | Conteúdo |
|---|---|---|
| `stremio-cache` | Stremio | cache, pins, certificados e estado torrent |
| `stremio-config` | Web Admin | configurações editadas no painel; leitura pelo Stremio |
| `webadmin-data` | Web Admin | auditoria, resultados de update e estado do painel |
| `pihole-etc` | Pi-hole | configuração e base de dados Pi-hole |
| `pihole-dnsmasq` | Pi-hole | regras DNS/DHCP adicionais |

## Instalação

```bash
cp .env.example .env
nano .env
docker compose config
docker compose up -d --build
docker compose ps
```

Acessos: Web Admin `http://IP:8090`, Player `http://IP:8080`, API `http://IP:11470` e Pi-hole `http://IP:8053/admin/`.

As alterações em **All Configuration** são guardadas no volume `stremio-config`. Reinicie o Stremio pelo botão do painel para as aplicar. Não use `docker compose down -v` numa actualização.

## Actualização pelo painel

O Web Admin descarrega directamente a branch `main` do fork, valida o arquivo, reinsere apenas o adaptador de configuração externa e constrói a nova imagem do Stremio. Se o ponto de integração deixar de existir, o processo aborta sem alterar a imagem activa. Após uma compilação com sucesso, active a imagem com:

```bash
docker compose up -d --force-recreate stremio-libtorrent-server
```

O Web Admin continua activo durante esta operação.

## Segurança

O Web Admin possui acesso ao socket Docker para consultar logs, reiniciar o Stremio e construir actualizações. Por esse motivo, a porta 8090 deve ficar limitada à LAN/VPN e nunca exposta à Internet. O Pi-hole está sem palavra-passe por decisão do operador e exige a mesma restrição.
