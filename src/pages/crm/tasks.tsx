import React from "react";
import { Table, Typography, Tag, Space, Button } from "antd";
import { PlusOutlined, EyeOutlined, EditOutlined, DeleteOutlined, ProjectOutlined } from "@ant-design/icons";
import { useTable } from "@refinedev/antd";

export interface Task {
    id: number;
    name: string;
    description?: string;
    priority?: string;
    stage?: string;
    user?: string;
    partner?: string;
    date_deadline?: string;
    created_at?: string;
}

const getPriorityTag = (priority?: string) => {
    if (!priority) return null;
    let color = "default";
    if (priority === "Alta") color = "red";
    else if (priority === "Media") color = "orange";
    else if (priority === "Baja") color = "green";
    return <Tag color={color}>{priority}</Tag>;
};

export const Tasks: React.FC = () => {
    const { tableProps, searchFormProps } = useTable<Task>({
        resource: "tasks",
        initialSorter: [{ field: "date_deadline", order: "asc" }],
        initialFilter: [],
        syncWithLocation: true,
    });

    return (
        <div>
            <Space style={{ marginBottom: 16, width: "100%", justifyContent: "space-between" }}>
                <Typography.Title level={3} style={{ margin: 0 }}>
                    <ProjectOutlined style={{ marginRight: 8 }} /> Tareas
                </Typography.Title>
                <Button type="primary" icon={<PlusOutlined />}>Nueva Tarea</Button>
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
                        title: "Descripción",
                        dataIndex: "description",
                        key: "description",
                        ellipsis: true,
                    },
                    {
                        title: "Prioridad",
                        dataIndex: "priority",
                        key: "priority",
                        render: getPriorityTag,
                    },
                    {
                        title: "Etapa",
                        dataIndex: "stage",
                        key: "stage",
                    },
                    {
                        title: "Responsable",
                        dataIndex: "user",
                        key: "user",
                    },
                    {
                        title: "Cliente",
                        dataIndex: "partner",
                        key: "partner",
                    },
                    {
                        title: "Fecha límite",
                        dataIndex: "date_deadline",
                        key: "date_deadline",
                        sorter: true,
                        render: (date?: string) => date ? new Date(date).toLocaleDateString() : "-",
                    },
                    {
                        title: "Acciones",
                        key: "actions",
                        render: (_, record: Task) => (
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

export default Tasks;
