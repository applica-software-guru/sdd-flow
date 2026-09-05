import { Navigate, useParams } from 'react-router-dom';

export default function ListPage() {
  const { tenantId } = useParams();
  return <Navigate to={`/tenants/${tenantId}`} replace />;
}
