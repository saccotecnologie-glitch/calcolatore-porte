create policy "clienti_select"
on public.clienti_satec
for select
using (true);

create policy "clienti_insert"
on public.clienti_satec
for insert
with check (true);

create policy "clienti_update"
on public.clienti_satec
for update
using (true);

create policy "clienti_delete"
on public.clienti_satec
for delete
using (true);
