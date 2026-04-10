--
-- PostgreSQL database dump
--

\restrict pgKgsoOShMsrsNGcxOxMBQQJ6gXtePakVUewuFFS7qSrb9tEGQYJdu4QbCHIB4M

-- Dumped from database version 16.13 (Debian 16.13-1.pgdg13+1)
-- Dumped by pg_dump version 16.13 (Debian 16.13-1.pgdg13+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: reservation_status; Type: TYPE; Schema: public; Owner: flashsale
--

CREATE TYPE public.reservation_status AS ENUM (
    'active',
    'confirmed',
    'cancelled',
    'expired'
);


ALTER TYPE public.reservation_status OWNER TO flashsale;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: flashsale
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO flashsale;

--
-- Name: outbox_events; Type: TABLE; Schema: public; Owner: flashsale
--

CREATE TABLE public.outbox_events (
    id uuid NOT NULL,
    event_type character varying(100) NOT NULL,
    payload json NOT NULL,
    occurred_at timestamp with time zone DEFAULT now() NOT NULL,
    reservation_id uuid NOT NULL
);


ALTER TABLE public.outbox_events OWNER TO flashsale;

--
-- Name: products; Type: TABLE; Schema: public; Owner: flashsale
--

CREATE TABLE public.products (
    id uuid NOT NULL,
    name character varying(200) NOT NULL,
    stock integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_products_stock_non_negative CHECK ((stock >= 0))
);


ALTER TABLE public.products OWNER TO flashsale;

--
-- Name: reservations; Type: TABLE; Schema: public; Owner: flashsale
--

CREATE TABLE public.reservations (
    id uuid NOT NULL,
    user_id character varying(100) NOT NULL,
    product_id uuid NOT NULL,
    status public.reservation_status NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    expires_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.reservations OWNER TO flashsale;

--
-- Name: structured_events; Type: TABLE; Schema: public; Owner: flashsale
--

CREATE TABLE public.structured_events (
    event_id uuid NOT NULL,
    event_type character varying(100) NOT NULL,
    occurred_at timestamp with time zone NOT NULL,
    reservation_id uuid,
    user_id character varying(100),
    product_id uuid,
    reservation_status character varying(50),
    expires_at timestamp with time zone,
    ttl_seconds integer,
    outbox_event_type character varying(100),
    metric_name character varying(100),
    extra json NOT NULL
);


ALTER TABLE public.structured_events OWNER TO flashsale;

--
-- Name: train_dataset_cursors; Type: TABLE; Schema: public; Owner: flashsale
--

CREATE TABLE public.train_dataset_cursors (
    name character varying(50) NOT NULL,
    last_final_event_at timestamp with time zone NOT NULL
);


ALTER TABLE public.train_dataset_cursors OWNER TO flashsale;

--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: flashsale
--

COPY public.alembic_version (version_num) FROM stdin;
0001_initial
\.


--
-- Data for Name: outbox_events; Type: TABLE DATA; Schema: public; Owner: flashsale
--

COPY public.outbox_events (id, event_type, payload, occurred_at, reservation_id) FROM stdin;
f9be260b-6a9e-4676-81bc-02ef09fd4062	reservation_confirmed	{"reservation_id": "7e70c67f-ea48-4dc6-8add-ae5fe4c79157", "user_id": "u1", "product_id": "3cb5373a-f115-4426-9b84-ecc1ee527c64", "confirmed_at": "2026-04-09T19:01:34.174581+00:00"}	2026-04-09 19:01:34.173543+00	7e70c67f-ea48-4dc6-8add-ae5fe4c79157
b4c4119c-93e9-4ae3-a019-05eb3ed3d450	reservation_confirmed	{"reservation_id": "437715ba-a2fb-4d67-b853-ef4ad6c02aa8", "user_id": "u2", "product_id": "ff3e7282-e3d0-4db3-a4e7-c1c5879e03b7", "confirmed_at": "2026-04-10T07:43:13.943607+00:00"}	2026-04-10 07:43:13.94161+00	437715ba-a2fb-4d67-b853-ef4ad6c02aa8
\.


--
-- Data for Name: products; Type: TABLE DATA; Schema: public; Owner: flashsale
--

COPY public.products (id, name, stock, created_at) FROM stdin;
063a24d4-5b28-4116-9c6f-b023d3d8466b	test-from-agent	5	2026-04-09 18:28:33.179104+00
bf73a5d8-c293-4282-acae-539d27fb7115	lozhka	33	2026-04-09 18:30:38.92586+00
2e792be4-62a6-4a4f-9184-b7ab29bad0eb	wwww	13	2026-04-09 18:31:17.442358+00
48613c94-58bc-454b-a9ed-a27759b303e8	siska	17	2026-04-09 18:31:26.730868+00
3ce933d0-8fa9-4c9b-acbe-ef2e7ebc3ce9	stariy	1	2026-04-09 18:31:53.838462+00
2061358f-3b1e-47f7-9c88-e770d082808e	bills	4	2026-04-09 18:49:07.996844+00
3cb5373a-f115-4426-9b84-ecc1ee527c64	test1	2	2026-04-09 19:00:31.253295+00
181e5989-6959-4aff-97ee-4edd6809d72e	bog	1	2026-04-09 18:31:59.267196+00
601a7f09-5028-4411-ba71-05f4ec884170	phone	3	2026-04-09 18:30:28.402962+00
ff3e7282-e3d0-4db3-a4e7-c1c5879e03b7	bills	3	2026-04-09 18:49:33.19672+00
\.


--
-- Data for Name: reservations; Type: TABLE DATA; Schema: public; Owner: flashsale
--

COPY public.reservations (id, user_id, product_id, status, created_at, expires_at, updated_at) FROM stdin;
7e70c67f-ea48-4dc6-8add-ae5fe4c79157	u1	3cb5373a-f115-4426-9b84-ecc1ee527c64	confirmed	2026-04-09 19:01:18.871704+00	2026-04-09 19:06:18.853186+00	2026-04-09 19:01:34.173543+00
642d2394-7df8-4c57-91ae-c508864d8778	u2	3cb5373a-f115-4426-9b84-ecc1ee527c64	cancelled	2026-04-09 19:02:03.181575+00	2026-04-09 19:07:03.18027+00	2026-04-09 19:02:14.989165+00
f89630be-97f8-4653-9253-2f1e04583e04	user-1	181e5989-6959-4aff-97ee-4edd6809d72e	expired	2026-04-09 18:39:31.437561+00	2026-04-09 18:44:31.422544+00	2026-04-09 19:05:08.118256+00
07c8a196-3ce9-4865-a658-fb0485750c05	user-1	601a7f09-5028-4411-ba71-05f4ec884170	expired	2026-04-09 18:41:02.98929+00	2026-04-09 18:46:02.981706+00	2026-04-09 19:05:08.12861+00
0b5c072d-4809-4e4b-bfad-f7cfb9b4724e	user-2	601a7f09-5028-4411-ba71-05f4ec884170	expired	2026-04-09 18:41:46.734256+00	2026-04-09 18:46:46.726807+00	2026-04-09 19:05:15.579415+00
904725f0-92e4-49f9-8bae-bd0bd537156b	user-3	601a7f09-5028-4411-ba71-05f4ec884170	expired	2026-04-09 18:41:50.320878+00	2026-04-09 18:46:50.319694+00	2026-04-09 19:05:15.586798+00
437715ba-a2fb-4d67-b853-ef4ad6c02aa8	u2	ff3e7282-e3d0-4db3-a4e7-c1c5879e03b7	confirmed	2026-04-10 07:42:38.703775+00	2026-04-10 07:47:38.694013+00	2026-04-10 07:43:13.94161+00
\.


--
-- Data for Name: structured_events; Type: TABLE DATA; Schema: public; Owner: flashsale
--

COPY public.structured_events (event_id, event_type, occurred_at, reservation_id, user_id, product_id, reservation_status, expires_at, ttl_seconds, outbox_event_type, metric_name, extra) FROM stdin;
4237def3-e831-409f-862d-c7cd10240751	reservation_created	2026-04-09 18:39:31.457861+00	f89630be-97f8-4653-9253-2f1e04583e04	user-1	181e5989-6959-4aff-97ee-4edd6809d72e	active	2026-04-09 18:44:31.422544+00	300	\N	\N	{}
5d67abdb-5db7-44bf-9b6f-b68c11b5eadc	reservation_ttl_registered	2026-04-09 18:39:31.47079+00	f89630be-97f8-4653-9253-2f1e04583e04	user-1	181e5989-6959-4aff-97ee-4edd6809d72e	\N	2026-04-09 18:44:31.422544+00	300	\N	\N	{}
2bc0459b-55d8-4e1a-b20e-5c679412493c	metrics_counter_incremented	2026-04-09 18:39:31.473154+00	f89630be-97f8-4653-9253-2f1e04583e04	user-1	181e5989-6959-4aff-97ee-4edd6809d72e	active	\N	\N	\N	created	{}
e69ec4a9-3e45-4bf9-83e4-cf64057c0455	reservation_created	2026-04-09 18:41:02.999062+00	07c8a196-3ce9-4865-a658-fb0485750c05	user-1	601a7f09-5028-4411-ba71-05f4ec884170	active	2026-04-09 18:46:02.981706+00	300	\N	\N	{}
54fc8db8-1eb4-4d9d-b2ff-c361ae8ab78f	reservation_ttl_registered	2026-04-09 18:41:03.002658+00	07c8a196-3ce9-4865-a658-fb0485750c05	user-1	601a7f09-5028-4411-ba71-05f4ec884170	\N	2026-04-09 18:46:02.981706+00	300	\N	\N	{}
1f9cab86-5907-41a1-bd83-dc27f1f4fa1e	metrics_counter_incremented	2026-04-09 18:41:03.004299+00	07c8a196-3ce9-4865-a658-fb0485750c05	user-1	601a7f09-5028-4411-ba71-05f4ec884170	active	\N	\N	\N	created	{}
81776348-09e1-4966-b05d-63406803dff6	reservation_created	2026-04-09 18:41:46.742837+00	0b5c072d-4809-4e4b-bfad-f7cfb9b4724e	user-2	601a7f09-5028-4411-ba71-05f4ec884170	active	2026-04-09 18:46:46.726807+00	300	\N	\N	{}
3f2c1de8-fc8f-4118-97f4-caeacc2d6544	reservation_ttl_registered	2026-04-09 18:41:46.745924+00	0b5c072d-4809-4e4b-bfad-f7cfb9b4724e	user-2	601a7f09-5028-4411-ba71-05f4ec884170	\N	2026-04-09 18:46:46.726807+00	300	\N	\N	{}
dc92d98c-94da-4039-8d03-c7a138e72de1	metrics_counter_incremented	2026-04-09 18:41:46.747559+00	0b5c072d-4809-4e4b-bfad-f7cfb9b4724e	user-2	601a7f09-5028-4411-ba71-05f4ec884170	active	\N	\N	\N	created	{}
1bcab70a-2250-408a-94c8-5504c32b87ae	reservation_created	2026-04-09 18:41:50.32735+00	904725f0-92e4-49f9-8bae-bd0bd537156b	user-3	601a7f09-5028-4411-ba71-05f4ec884170	active	2026-04-09 18:46:50.319694+00	300	\N	\N	{}
0faa3db0-8521-4847-a565-ad0a6d29b25b	reservation_ttl_registered	2026-04-09 18:41:50.329272+00	904725f0-92e4-49f9-8bae-bd0bd537156b	user-3	601a7f09-5028-4411-ba71-05f4ec884170	\N	2026-04-09 18:46:50.319694+00	300	\N	\N	{}
a2983e51-328e-4d64-963b-ae0cae3f42d6	metrics_counter_incremented	2026-04-09 18:41:50.330634+00	904725f0-92e4-49f9-8bae-bd0bd537156b	user-3	601a7f09-5028-4411-ba71-05f4ec884170	active	\N	\N	\N	created	{}
d8f3566a-84b7-46bc-895a-88bf0d16b096	reservation_created	2026-04-09 19:01:18.88595+00	7e70c67f-ea48-4dc6-8add-ae5fe4c79157	u1	3cb5373a-f115-4426-9b84-ecc1ee527c64	active	2026-04-09 19:06:18.853186+00	300	\N	\N	{}
d5cd3d90-37c1-45e6-9710-c6c0437a4522	reservation_ttl_registered	2026-04-09 19:01:18.890298+00	7e70c67f-ea48-4dc6-8add-ae5fe4c79157	u1	3cb5373a-f115-4426-9b84-ecc1ee527c64	\N	2026-04-09 19:06:18.853186+00	300	\N	\N	{}
86ef4cda-ab91-4118-9ab7-474da50f747a	metrics_counter_incremented	2026-04-09 19:01:18.89198+00	7e70c67f-ea48-4dc6-8add-ae5fe4c79157	u1	3cb5373a-f115-4426-9b84-ecc1ee527c64	active	\N	\N	\N	created	{}
fa98b6c8-4f9e-40d4-b86a-be46cb1152f3	reservation_confirmed	2026-04-09 19:01:34.182019+00	7e70c67f-ea48-4dc6-8add-ae5fe4c79157	u1	3cb5373a-f115-4426-9b84-ecc1ee527c64	confirmed	\N	\N	\N	\N	{}
a9ef7028-0ca5-4f56-9aad-fea1e2479308	reservation_confirmation_outbox_written	2026-04-09 19:01:34.183879+00	7e70c67f-ea48-4dc6-8add-ae5fe4c79157	u1	3cb5373a-f115-4426-9b84-ecc1ee527c64	\N	\N	\N	reservation_confirmed	\N	{}
e479dcf8-7bea-4cfc-b85d-00ba3bc1f91d	metrics_counter_incremented	2026-04-09 19:01:34.185338+00	7e70c67f-ea48-4dc6-8add-ae5fe4c79157	u1	3cb5373a-f115-4426-9b84-ecc1ee527c64	confirmed	\N	\N	\N	confirmed	{}
84df7971-4282-4171-a6e9-930dc937c0f8	reservation_created	2026-04-09 19:02:03.192744+00	642d2394-7df8-4c57-91ae-c508864d8778	u2	3cb5373a-f115-4426-9b84-ecc1ee527c64	active	2026-04-09 19:07:03.18027+00	300	\N	\N	{}
607b20ba-171d-4411-a1f7-6128389ccda6	reservation_ttl_registered	2026-04-09 19:02:03.195711+00	642d2394-7df8-4c57-91ae-c508864d8778	u2	3cb5373a-f115-4426-9b84-ecc1ee527c64	\N	2026-04-09 19:07:03.18027+00	300	\N	\N	{}
1d708dc1-7e82-4f5f-a67d-317a89cc215c	metrics_counter_incremented	2026-04-09 19:02:03.19741+00	642d2394-7df8-4c57-91ae-c508864d8778	u2	3cb5373a-f115-4426-9b84-ecc1ee527c64	active	\N	\N	\N	created	{}
b6e8bd93-9f69-41d8-82aa-18e39e9d3391	reservation_cancelled	2026-04-09 19:02:14.995855+00	642d2394-7df8-4c57-91ae-c508864d8778	u2	3cb5373a-f115-4426-9b84-ecc1ee527c64	cancelled	\N	\N	\N	\N	{}
6c0b0e95-1135-42f0-835b-8983b45c18f7	metrics_counter_incremented	2026-04-09 19:02:14.998514+00	642d2394-7df8-4c57-91ae-c508864d8778	u2	3cb5373a-f115-4426-9b84-ecc1ee527c64	cancelled	\N	\N	\N	cancelled	{}
88d893a1-2e05-4630-ad26-91cef2a97987	expired_reservations_sync_started	2026-04-09 19:05:08.102345+00	\N	\N	\N	\N	\N	\N	\N	\N	{}
3cbb9d47-a457-41f7-98d3-b53d321f299c	reservation_expired	2026-04-09 19:05:08.12545+00	f89630be-97f8-4653-9253-2f1e04583e04	user-1	181e5989-6959-4aff-97ee-4edd6809d72e	expired	\N	\N	\N	\N	{}
abd828f0-613d-4d53-ad7d-45111efd4491	metrics_counter_incremented	2026-04-09 19:05:08.127414+00	f89630be-97f8-4653-9253-2f1e04583e04	user-1	181e5989-6959-4aff-97ee-4edd6809d72e	expired	\N	\N	\N	expired	{}
03fc57b0-1406-4d57-93a5-0be9ca941ae4	reservation_expired	2026-04-09 19:05:08.130872+00	07c8a196-3ce9-4865-a658-fb0485750c05	user-1	601a7f09-5028-4411-ba71-05f4ec884170	expired	\N	\N	\N	\N	{}
b8c9fca6-1cb7-4ee0-8b43-a99a0377865b	metrics_counter_incremented	2026-04-09 19:05:08.132423+00	07c8a196-3ce9-4865-a658-fb0485750c05	user-1	601a7f09-5028-4411-ba71-05f4ec884170	expired	\N	\N	\N	expired	{}
932aae04-5c0a-4e3f-bc65-8b297d31bd47	expired_reservations_sync_completed	2026-04-09 19:05:08.13319+00	\N	\N	\N	\N	\N	\N	\N	\N	{"processed": 2, "expired": 2}
c59739c3-c761-47ca-b449-00b51e05d069	expired_reservations_sync_started	2026-04-09 19:05:15.575485+00	\N	\N	\N	\N	\N	\N	\N	\N	{}
36fabea9-81e0-46fd-b308-4388a6134667	reservation_expired	2026-04-09 19:05:15.584293+00	0b5c072d-4809-4e4b-bfad-f7cfb9b4724e	user-2	601a7f09-5028-4411-ba71-05f4ec884170	expired	\N	\N	\N	\N	{}
a6485cbd-09e5-4cff-8567-a68331182a23	metrics_counter_incremented	2026-04-09 19:05:15.585776+00	0b5c072d-4809-4e4b-bfad-f7cfb9b4724e	user-2	601a7f09-5028-4411-ba71-05f4ec884170	expired	\N	\N	\N	expired	{}
02d2b804-3eeb-49cc-abe1-b568f2fed870	reservation_expired	2026-04-09 19:05:15.58877+00	904725f0-92e4-49f9-8bae-bd0bd537156b	user-3	601a7f09-5028-4411-ba71-05f4ec884170	expired	\N	\N	\N	\N	{}
4099614f-5db5-4e20-9235-22e2c9d14f6f	metrics_counter_incremented	2026-04-09 19:05:15.590162+00	904725f0-92e4-49f9-8bae-bd0bd537156b	user-3	601a7f09-5028-4411-ba71-05f4ec884170	expired	\N	\N	\N	expired	{}
b4a69093-c32b-4967-98e3-d20be4da95fb	expired_reservations_sync_completed	2026-04-09 19:05:15.590892+00	\N	\N	\N	\N	\N	\N	\N	\N	{"processed": 2, "expired": 2}
ad252fd3-cf7e-4efd-a666-0afd8b38d20d	expired_reservations_sync_started	2026-04-09 19:05:18.597386+00	\N	\N	\N	\N	\N	\N	\N	\N	{}
1c4c3e34-50c2-491d-84ac-8ad52d54baa9	expired_reservations_sync_completed	2026-04-09 19:05:18.602902+00	\N	\N	\N	\N	\N	\N	\N	\N	{"processed": 0, "expired": 0}
6e41289f-2baa-4ac6-8aa4-c39d96327090	expired_reservations_sync_started	2026-04-09 19:05:21.769594+00	\N	\N	\N	\N	\N	\N	\N	\N	{}
537cd7de-2c2b-42a0-9d24-0cbdc4f4b27a	expired_reservations_sync_completed	2026-04-09 19:05:21.772671+00	\N	\N	\N	\N	\N	\N	\N	\N	{"processed": 0, "expired": 0}
d1973d15-0081-49e2-b78b-f62fc83abcfc	expired_reservations_sync_started	2026-04-09 19:05:22.897399+00	\N	\N	\N	\N	\N	\N	\N	\N	{}
a083e956-9fec-43b4-92cb-9ae6cda7d30c	expired_reservations_sync_completed	2026-04-09 19:05:22.903197+00	\N	\N	\N	\N	\N	\N	\N	\N	{"processed": 0, "expired": 0}
506512f9-04dd-4d86-bf03-6dddcca2fe39	expired_reservations_sync_started	2026-04-09 19:05:26.75443+00	\N	\N	\N	\N	\N	\N	\N	\N	{}
f81dfacb-418f-42d9-8acd-163dedc16616	expired_reservations_sync_completed	2026-04-09 19:05:26.761591+00	\N	\N	\N	\N	\N	\N	\N	\N	{"processed": 0, "expired": 0}
002ba8cd-79bb-4e39-91e2-5a9ab6a47f66	expired_reservations_sync_started	2026-04-09 19:05:30.105079+00	\N	\N	\N	\N	\N	\N	\N	\N	{}
6a887146-e19f-4baa-91d1-d3d4bed9c477	expired_reservations_sync_completed	2026-04-09 19:05:30.111272+00	\N	\N	\N	\N	\N	\N	\N	\N	{"processed": 0, "expired": 0}
10ce1e23-5e61-4156-8044-d8b0284bab09	expired_reservations_sync_started	2026-04-09 19:05:39.389696+00	\N	\N	\N	\N	\N	\N	\N	\N	{}
a7b3e9b2-6d82-47d2-9759-86d0f796e6d2	expired_reservations_sync_completed	2026-04-09 19:05:39.402322+00	\N	\N	\N	\N	\N	\N	\N	\N	{"processed": 0, "expired": 0}
b59cbc00-2b3a-4ecd-bea3-50ddd2772c72	expired_reservations_sync_started	2026-04-09 19:05:47.313103+00	\N	\N	\N	\N	\N	\N	\N	\N	{}
f44da6e2-bf8b-451f-84b4-7fbe28eafac6	expired_reservations_sync_completed	2026-04-09 19:05:47.318709+00	\N	\N	\N	\N	\N	\N	\N	\N	{"processed": 0, "expired": 0}
7a5e6daa-e5c6-4872-81f6-a2b8f8b449f3	reservation_created	2026-04-10 07:42:38.721717+00	437715ba-a2fb-4d67-b853-ef4ad6c02aa8	u2	ff3e7282-e3d0-4db3-a4e7-c1c5879e03b7	active	2026-04-10 07:47:38.694013+00	300	\N	\N	{}
50fd303c-b345-4ad5-9ba3-47f4651a37ae	reservation_ttl_registered	2026-04-10 07:42:38.73605+00	437715ba-a2fb-4d67-b853-ef4ad6c02aa8	u2	ff3e7282-e3d0-4db3-a4e7-c1c5879e03b7	\N	2026-04-10 07:47:38.694013+00	300	\N	\N	{}
de6808c3-4bb6-4501-97ab-ea23ea7110c7	metrics_counter_incremented	2026-04-10 07:42:38.737847+00	437715ba-a2fb-4d67-b853-ef4ad6c02aa8	u2	ff3e7282-e3d0-4db3-a4e7-c1c5879e03b7	active	\N	\N	\N	created	{}
d54e8041-7e38-4bee-bcf9-5fd71690552e	reservation_confirmed	2026-04-10 07:43:13.951553+00	437715ba-a2fb-4d67-b853-ef4ad6c02aa8	u2	ff3e7282-e3d0-4db3-a4e7-c1c5879e03b7	confirmed	\N	\N	\N	\N	{}
1819dc67-8a97-4385-9f66-9a81ff03035e	reservation_confirmation_outbox_written	2026-04-10 07:43:13.954391+00	437715ba-a2fb-4d67-b853-ef4ad6c02aa8	u2	ff3e7282-e3d0-4db3-a4e7-c1c5879e03b7	\N	\N	\N	reservation_confirmed	\N	{}
2c49c7f4-dda0-4531-ac2a-5ba2423a9344	metrics_counter_incremented	2026-04-10 07:43:13.955751+00	437715ba-a2fb-4d67-b853-ef4ad6c02aa8	u2	ff3e7282-e3d0-4db3-a4e7-c1c5879e03b7	confirmed	\N	\N	\N	confirmed	{}
\.


--
-- Data for Name: train_dataset_cursors; Type: TABLE DATA; Schema: public; Owner: flashsale
--

COPY public.train_dataset_cursors (name, last_final_event_at) FROM stdin;
default	2026-04-10 07:43:13.951553+00
\.


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: flashsale
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: outbox_events outbox_events_pkey; Type: CONSTRAINT; Schema: public; Owner: flashsale
--

ALTER TABLE ONLY public.outbox_events
    ADD CONSTRAINT outbox_events_pkey PRIMARY KEY (id);


--
-- Name: products products_pkey; Type: CONSTRAINT; Schema: public; Owner: flashsale
--

ALTER TABLE ONLY public.products
    ADD CONSTRAINT products_pkey PRIMARY KEY (id);


--
-- Name: reservations reservations_pkey; Type: CONSTRAINT; Schema: public; Owner: flashsale
--

ALTER TABLE ONLY public.reservations
    ADD CONSTRAINT reservations_pkey PRIMARY KEY (id);


--
-- Name: structured_events structured_events_pkey; Type: CONSTRAINT; Schema: public; Owner: flashsale
--

ALTER TABLE ONLY public.structured_events
    ADD CONSTRAINT structured_events_pkey PRIMARY KEY (event_id);


--
-- Name: train_dataset_cursors train_dataset_cursors_pkey; Type: CONSTRAINT; Schema: public; Owner: flashsale
--

ALTER TABLE ONLY public.train_dataset_cursors
    ADD CONSTRAINT train_dataset_cursors_pkey PRIMARY KEY (name);


--
-- Name: ix_reservations_product_id; Type: INDEX; Schema: public; Owner: flashsale
--

CREATE INDEX ix_reservations_product_id ON public.reservations USING btree (product_id);


--
-- Name: ix_reservations_status; Type: INDEX; Schema: public; Owner: flashsale
--

CREATE INDEX ix_reservations_status ON public.reservations USING btree (status);


--
-- Name: ix_reservations_user_id; Type: INDEX; Schema: public; Owner: flashsale
--

CREATE INDEX ix_reservations_user_id ON public.reservations USING btree (user_id);


--
-- Name: ix_structured_events_reservation; Type: INDEX; Schema: public; Owner: flashsale
--

CREATE INDEX ix_structured_events_reservation ON public.structured_events USING btree (reservation_id);


--
-- Name: ix_structured_events_type_time; Type: INDEX; Schema: public; Owner: flashsale
--

CREATE INDEX ix_structured_events_type_time ON public.structured_events USING btree (event_type, occurred_at);


--
-- Name: uq_active_reservation_per_user_product; Type: INDEX; Schema: public; Owner: flashsale
--

CREATE UNIQUE INDEX uq_active_reservation_per_user_product ON public.reservations USING btree (user_id, product_id) WHERE (status = 'active'::public.reservation_status);


--
-- Name: outbox_events outbox_events_reservation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: flashsale
--

ALTER TABLE ONLY public.outbox_events
    ADD CONSTRAINT outbox_events_reservation_id_fkey FOREIGN KEY (reservation_id) REFERENCES public.reservations(id) ON DELETE CASCADE;


--
-- Name: reservations reservations_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: flashsale
--

ALTER TABLE ONLY public.reservations
    ADD CONSTRAINT reservations_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict pgKgsoOShMsrsNGcxOxMBQQJ6gXtePakVUewuFFS7qSrb9tEGQYJdu4QbCHIB4M

