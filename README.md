# Patinhado2

API REST para plataforma de adoção de pets, desenvolvida em Django REST Framework.

## Funcionalidades

### Autenticação

- **Registro e Login**: Criação de conta com retorno de tokens JWT (access + refresh)
- **Perfil de Usuário**: Visualização e edição dos dados pessoais (nome, email, telefone, endereço, foto)
- **Tokens JWT**: Obtenção, renovação e verificação de tokens

### Gerenciamento de Pets (Doadores)

- **Cadastro de Pet**: Adicionar animais para adoção com foto, nome, espécie, raça, idade e descrição
- **Edição de Pet**: Atualizar informações dos animais cadastrados
- **Exclusão de Pet**: Remover animais do sistema
- **Aprovação/Rejeição de Pedidos**: Gerenciar pedidos de adoção recebidos

### Pedidos de Adoção (Adotantes)

- **Solicitação de Adoção**: Enviar pedido para um animal disponível
- **Edição de Pedido**: Modificar dados do pedido enquanto estiver pendente
- **Cancelamento de Pedido**: Cancelar pedido pendente
- **Acompanhamento**: Visualizar status dos pedidos enviados

### Recursos Adicionais

- **Filtros**: Listagem de pets com filtros por espécie, status de adoção e doador
- **Validações de Negócio**: Garante que animais adotados tenham adotante definido; impede adoção de animal já adotado
- **Upload de Imagens**: Suporte a upload de fotos de pets e usuários
- **Documentação Automática**: Swagger UI disponível em `/api/docs/`
- **Testes Automatizados**: 25 testes cobrindo autenticação, pets e pedidos

## Workflow

O sistema de adoção funciona em três etapas via API:

1. **Doação**: Um usuário autenticado cadastra um pet para adoção (`POST /api/pets/`)
2. **Solicitação**: Outro usuário autenticado envia um pedido de adoção (`POST /api/pedidos/`)
3. **Aprovação**: O doador aprova ou rejeita o pedido (`POST /api/pedidos/<id>/aprovar/`)

### Endpoints da API

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| **Autenticação** | | |
| `POST` | `/api/auth/register/` | Registrar novo usuário |
| `POST` | `/api/auth/token/` | Obter tokens JWT (login) |
| `POST` | `/api/auth/token/refresh/` | Renovar access token |
| `POST` | `/api/auth/token/verify/` | Verificar token JWT |
| `GET/PUT/PATCH` | `/api/auth/profile/` | Gerenciar perfil do usuário |
| **Pets** | | |
| `GET` | `/api/pets/` | Listar pets (com filtros) |
| `POST` | `/api/pets/` | Cadastrar novo pet |
| `GET/PUT/PATCH/DELETE` | `/api/pets/<id>/` | Detalhar, editar ou excluir pet |
| **Pedidos de Adoção** | | |
| `GET/POST` | `/api/pedidos/` | Listar ou criar pedidos |
| `GET/PUT/PATCH/DELETE` | `/api/pedidos/<id>/` | Detalhar, editar ou excluir pedido |
| `POST` | `/api/pedidos/<id>/aprovar/` | Aprovar pedido (doador) |
| `POST` | `/api/pedidos/<id>/rejeitar/` | Rejeitar pedido (doador) |
| `POST` | `/api/pedidos/<id>/cancelar/` | Cancelar pedido (solicitante) |
| **Documentação** | | |
| `GET` | `/api/docs/` | Swagger UI interativo |
| `GET` | `/api/schema/` | Schema OpenAPI (YAML) |

## Tecnologias Utilizadas

- **Backend**: Django 6.0.4 + Django REST Framework
- **Autenticação**: JWT (djangorestframework-simplejwt)
- **Banco de Dados**: SQLite (desenvolvimento)
- **Imagens**: Pillow 12.2.0
- **Senhas**: Argon2 (argon2-cffi 25.1.0)
- **Documentação**: drf-spectacular (OpenAPI 3.0.3 + Swagger UI)
- **Ambiente**: python-dotenv

## Como Usar

### Pré-requisitos

- Python 3.10+

### Instalação Local

1. Clone o repositório:
   ```bash
   git clone <url-do-repositorio>
   cd Patinhado2/Patinhado
   ```

2. Crie um ambiente virtual:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate    # Windows
   ```

3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure as variáveis de ambiente:
   - Copie o arquivo `.env.example` para `.env`
   - Ajuste as configurações necessárias

5. Execute as migrações:
   ```bash
   python manage.py migrate
   ```

6. Crie um superusuário (opcional):
   ```bash
   python manage.py createsuperuser
   ```

7. Inicie o servidor:
   ```bash
   python manage.py runserver
   ```

8. Acesse no navegador:
   - API: http://127.0.0.1:8000/api/
   - Swagger UI: http://127.0.0.1:8000/api/docs/

### Executar Testes

```bash
python manage.py test
```

### Estrutura do Projeto

```
Patinhado2/
├── Patinhado/               # Projeto Django
│   ├── Patinhado/          # Configurações do projeto
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── ...
│   ├── backend/            # Aplicação principal (API)
│   │   ├── models.py      # Modelos: Usuario, Pet, PedidoAdocao
│   │   ├── views.py       # Views da API REST
│   │   ├── serializers.py # Serializadores DRF
│   │   ├── permissions.py # Permissões personalizadas
│   │   ├── urls.py        # Rotas da API
│   │   └── tests.py       # Testes automatizados
│   ├── frontend/           # Scaffold para frontend (futuro)
│   ├── manage.py
│   ├── .env.example
│   └── requirements.txt
├── schema.yml              # Schema OpenAPI exportado
└── LICENSE
```

## Desenvolvedores

- **Arthur Sardella**
- **Ana Marques**

## Licença

MIT License

---

## Disclaimer

Este trabalho foi desenvolvido com auxílio de inteligência artificial.

- **Modelo de IA**: Big Pickle (opencode/big-pickle)
- **Ferramenta**: OpenCode
