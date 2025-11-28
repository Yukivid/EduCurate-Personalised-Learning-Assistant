"use client";

import VideoSearch from '@/components/search/VideoSearch'
import React, { useEffect, useState } from "react";
import axios from "axios";

type UserInfo = {
  user_id: number;
  userName: string;
  firstName: string;
  lastName: string;
  email: string;
};

const Page = () => {
  const [userInfo, setUserInfo] = useState<UserInfo | null>(null);
  const [userLoading, setUserLoading] = useState(true);

  useEffect(() => {
    const fetchUserInfo = async () => {
      try {
        const userId = 1;
        const response = await axios.get<UserInfo>(
          `http://localhost:8000/user-info/${userId}`
        );
        setUserInfo(response.data);
      } catch (error) {
        console.error("Error fetching user info:", error);
      } finally {
        setUserLoading(false);
      }
    };

    fetchUserInfo();
  }, []);

  if (userLoading) return <div>Loading...</div>;
  if (!userInfo) return <div>Unable to load user info.</div>;

  return (
    <div>
      <VideoSearch userName={userInfo.userName} />
    </div>
  );
}

export default Page;
