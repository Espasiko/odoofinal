import React from "react";
import { Table, Typography, Tag, Space, Button } from "antd";
import { PlusOutlined, EyeOutlined, EditOutlined, DeleteOutlined, ShopOutlined } from "@ant-design/icons";
import { useTable } from "@refinedev/antd";

export interface Company {
    id: number;
    name: string;
    email?: string;
    phone?: string;
    website?: string;
    city?: string;
    country?: string;
    industry?: string;
    created_at?: string;
}

const getIndustryTag = (industry?: string) => {
    if (!industry) return null;
    return <Tag color="blue">{industry}</Tag>;
};

export const Companies: React.FC = () => {
    const { tableProps, searchFormProps } = useTable<Company>({
        resource: "companies",
        initialSorter: [{ field: "created_at", order: "desc" }],
        initialFilter: [],
        syncWithLocation: true,
    });

    return (
        <div>
            <Space style={{ marginBottom: 16, width: "100%", justifyContent: "space-between" }}>
                <Typography.Title level={3} style={{ margin: 0 }}>
                    <ShopOutlined style={{ marginRight: 8 }} /> Empresas
                </Typography.Title>
                <Button type="primary" icon={<PlusOutlined />}>Nueva Empresa</Button>
            </Space>
            <Table
                {...tableProps}
                rowKey="id"
                columns={[
                    {
                        title: "Nombre",
                        dataIndex: "name",
                        key: "name",
                        sorter: true,
                        render: (text: string) => <b>{text}</b>,
                    },
                    {
                        title: "Email",
                        dataIndex: "email",
                        key: "email",
                    },
                    {
                        title: "Teléfono",
                        dataIndex: "phone",
                        key: "phone",
                    },
                    {
                        title: "Web",
                        dataIndex: "website",
                        key: "website",
                        render: (url?: string) => url ? <a href={url} target="_blank" rel="noopener noreferrer">{url}</a> : "-",
                    },
                    {
                        title: "Ciudad",
                        dataIndex: "city",
                        key: "city",
                    },
                    {
                        title: "País",
                        dataIndex: "country",
                        key: "country",
                    },
                    {
                        title: "Industria",
                        dataIndex: "industry",
                        key: "industry",
                        render: getIndustryTag,
                    },
                    {
                        title: "Creado",
                        dataIndex: "created_at",
                        key: "created_at",
                        sorter: true,
                        render: (date?: string) => date ? new Date(date).toLocaleDateString() : "-",
                    },
                    {
                        title: "Acciones",
                        key: "actions",
                        render: (_, record: Company) => (
                            <Space>
                                <Button icon={<EyeOutlined />} size="small" />
                                <Button icon={<EditOutlined />} size="small" />
                                <Button icon={<DeleteOutlined />} size="small" danger />
                            </Space>
                        ),
                    },
                ]}
                pagination={{ pageSize: 10 }}
            />
        </div>
    );
}

export default Companies;
